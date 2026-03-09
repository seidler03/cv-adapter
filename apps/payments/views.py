import logging
import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import Subscription

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def upgrade_page(request):
    """Show the Pro upgrade / pricing page."""
    return render(request, 'payments/upgrade.html', {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'pro_price': settings.PRO_PLAN_PRICE,
    })


@login_required
def create_checkout_session(request):
    """Create a Stripe Checkout Session and redirect the user."""
    user = request.user

    # Retrieve or create Stripe customer
    sub, _ = Subscription.objects.get_or_create(user=user)
    if sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={'user_id': str(user.pk)},
        )
        customer_id = customer['id']
        sub.stripe_customer_id = customer_id
        sub.save(update_fields=['stripe_customer_id'])

    success_url = request.build_absolute_uri(reverse('payments:success'))
    cancel_url = request.build_absolute_uri(reverse('payments:upgrade'))

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': settings.STRIPE_PRO_PRICE_ID,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url,
        currency=settings.STRIPE_CURRENCY,
        metadata={'user_id': str(user.pk)},
    )
    return redirect(session.url, permanent=False)


@login_required
def checkout_success(request):
    """Post-payment landing page."""
    return render(request, 'payments/success.html')


@login_required
def cancel_subscription(request):
    """Cancel the user's Stripe subscription at period end."""
    if request.method != 'POST':
        return redirect('payments:upgrade')

    user = request.user
    try:
        sub = user.subscription
        if sub.stripe_subscription_id:
            stripe.Subscription.modify(
                sub.stripe_subscription_id,
                cancel_at_period_end=True,
            )
            sub.status = Subscription.STATUS_CANCELED
            sub.save(update_fields=['status'])
            from django.contrib import messages
            messages.success(request, 'Your subscription has been canceled. You will retain Pro access until the end of the billing period.')
    except Exception as exc:
        logger.error('Error canceling subscription for %s: %s', user.email, exc)
        from django.contrib import messages
        messages.error(request, 'Failed to cancel subscription. Please contact support.')

    return redirect('dashboard:index')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe webhook handler.
    Handles: checkout.session.completed, customer.subscription.updated,
             customer.subscription.deleted, invoice.payment_failed
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning('Stripe webhook signature error: %s', exc)
        return HttpResponse(status=400)

    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        _handle_checkout_completed(data)

    elif event_type in ('customer.subscription.updated', 'customer.subscription.created'):
        _handle_subscription_updated(data)

    elif event_type == 'customer.subscription.deleted':
        _handle_subscription_deleted(data)

    elif event_type == 'invoice.payment_failed':
        _handle_payment_failed(data)

    return HttpResponse(status=200)


# ── private helpers ────────────────────────────────────────────────────────────

def _handle_checkout_completed(session):
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    try:
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
        sub.stripe_subscription_id = subscription_id
        sub.plan = Subscription.PLAN_PRO
        sub.status = Subscription.STATUS_ACTIVE
        sub.save(update_fields=['stripe_subscription_id', 'plan', 'status'])
        logger.info('Subscription activated for customer %s', customer_id)
    except Subscription.DoesNotExist:
        logger.warning('checkout.session.completed: no subscription for customer %s', customer_id)


def _handle_subscription_updated(stripe_sub):
    sub_id = stripe_sub.get('id')
    status = stripe_sub.get('status')
    current_period_end = stripe_sub.get('current_period_end')

    from django.utils import timezone
    import datetime

    try:
        sub = Subscription.objects.get(stripe_subscription_id=sub_id)
    except Subscription.DoesNotExist:
        # Might arrive before checkout.session.completed; skip
        logger.debug('subscription.updated: unknown sub %s', sub_id)
        return

    status_map = {
        'active': Subscription.STATUS_ACTIVE,
        'canceled': Subscription.STATUS_CANCELED,
        'past_due': Subscription.STATUS_PAST_DUE,
        'unpaid': Subscription.STATUS_PAST_DUE,
        'incomplete': Subscription.STATUS_INACTIVE,
        'incomplete_expired': Subscription.STATUS_INACTIVE,
        'trialing': Subscription.STATUS_ACTIVE,
    }
    sub.status = status_map.get(status, Subscription.STATUS_INACTIVE)
    if sub.status == Subscription.STATUS_ACTIVE:
        sub.plan = Subscription.PLAN_PRO
    if current_period_end:
        sub.current_period_end = datetime.datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )
    sub.save()
    logger.info('Subscription %s updated to status=%s', sub_id, sub.status)


def _handle_subscription_deleted(stripe_sub):
    sub_id = stripe_sub.get('id')
    try:
        sub = Subscription.objects.get(stripe_subscription_id=sub_id)
        sub.plan = Subscription.PLAN_FREE
        sub.status = Subscription.STATUS_CANCELED
        sub.save(update_fields=['plan', 'status'])
        logger.info('Subscription %s canceled (deleted)', sub_id)
    except Subscription.DoesNotExist:
        logger.debug('subscription.deleted: unknown sub %s', sub_id)


def _handle_payment_failed(invoice):
    customer_id = invoice.get('customer')
    try:
        sub = Subscription.objects.get(stripe_customer_id=customer_id)
        sub.status = Subscription.STATUS_PAST_DUE
        sub.save(update_fields=['status'])
        logger.warning('Payment failed for customer %s', customer_id)
    except Subscription.DoesNotExist:
        pass
