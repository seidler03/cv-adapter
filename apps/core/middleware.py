from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings


class UsageLimitMiddleware:
    """
    Intercepts requests to the CV adaptation endpoint and checks
    whether the free-tier user has exceeded their monthly limit.
    """

    CHECKED_PATHS = ['/cv/adapt/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ── PAYWALL DESATIVADO (comentado para liberar acesso ilimitado) ──────────
        # if request.path in self.CHECKED_PATHS and request.method == 'POST':
        #     if request.user.is_authenticated:
        #         if not self._has_quota(request.user):
        #             from django.http import JsonResponse
        #             if request.headers.get('HX-Request'):
        #                 return JsonResponse(
        #                     {
        #                         'error': 'limit_reached',
        #                         'message': (
        #                             'You have reached your 3 free adaptations this month. '
        #                             'Upgrade to Pro for unlimited access.'
        #                         ),
        #                     },
        #                     status=402,
        #                 )
        #             return redirect('payments:upgrade')
        # ─────────────────────────────────────────────────────────────────────────
        return self.get_response(request)

    def _has_quota(self, user):
        """Return True if the user may still run an adaptation."""
        # Pro subscribers have no limit
        try:
            sub = user.subscription
            if sub.is_active and sub.plan == 'pro':
                return True
        except Exception:
            pass

        # Count this calendar month's adaptations
        from apps.cv_adapter.models import JobApplication
        now = timezone.now()
        count = JobApplication.objects.filter(
            user=user,
            created_at__year=now.year,
            created_at__month=now.month,
        ).count()
        return count < settings.FREE_PLAN_MONTHLY_LIMIT
