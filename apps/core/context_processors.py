from django.utils import timezone


def subscription_context(request):
    """Inject subscription and usage info into every template."""
    context = {
        'is_pro': False,
        'monthly_usage': 0,
        'monthly_limit': 3,
    }
    if request.user.is_authenticated:
        try:
            sub = request.user.subscription
            context['is_pro'] = sub.is_active and sub.plan == 'pro'
        except Exception:
            pass

        from apps.cv_adapter.models import JobApplication
        from django.conf import settings
        now = timezone.now()
        context['monthly_usage'] = JobApplication.objects.filter(
            user=request.user,
            created_at__year=now.year,
            created_at__month=now.month,
        ).count()
        context['monthly_limit'] = settings.FREE_PLAN_MONTHLY_LIMIT

    return context
