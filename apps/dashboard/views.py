from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings

from apps.cv_adapter.models import CVBase, JobApplication


@login_required
def dashboard_index(request):
    """Main dashboard: summary stats + recent applications."""
    user = request.user
    now = timezone.now()

    cv_bases = CVBase.objects.filter(user=user)
    recent_apps = JobApplication.objects.filter(
        user=user, status=JobApplication.STATUS_DONE
    ).select_related('cv_base')[:5]

    monthly_count = JobApplication.objects.filter(
        user=user,
        created_at__year=now.year,
        created_at__month=now.month,
    ).count()

    total_apps = JobApplication.objects.filter(user=user, status=JobApplication.STATUS_DONE)
    avg_score = 0
    if total_apps.exists():
        avg_score = round(sum(a.score_match for a in total_apps) / total_apps.count())

    # Subscription / usage
    is_pro = getattr(user, 'is_pro', False) or (
        hasattr(user, 'subscription') and user.subscription.is_active
    )
    monthly_limit = settings.FREE_PLAN_MONTHLY_LIMIT
    monthly_usage = monthly_count

    stats = [
        ('CVs uploaded', cv_bases.count(), 'text-indigo-400'),
        ('Total adaptations', total_apps.count(), 'text-purple-400'),
        ('This month', monthly_count, 'text-teal-400'),
        ('Avg. match score', f'{avg_score}%', 'text-green-400'),
    ]

    return render(request, 'dashboard/index.html', {
        'cv_bases': cv_bases,
        'recent_apps': recent_apps,
        'stats': stats,
        'is_pro': is_pro,
        'monthly_usage': monthly_usage,
        'monthly_limit': monthly_limit,
    })
