import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import JobApplication
from .forms import JobApplicationForm, StatusUpdateForm


@login_required
def tracker_list(request):
    """Main tracker view: metrics, table, filters."""
    qs = JobApplication.objects.filter(user=request.user)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Stats
    all_apps = JobApplication.objects.filter(user=request.user)
    total = all_apps.count()
    in_progress = all_apps.filter(
        status__in=['screening', 'interview_1', 'interview_2', 'technical']
    ).count()
    offers = all_apps.filter(status='offer').count()
    responded = all_apps.exclude(status__in=['applied', 'ghosted']).count()
    response_rate = round((responded / total * 100) if total else 0)

    # Weekly chart data (last 8 weeks)
    from datetime import date, timedelta
    weeks_labels = []
    weeks_data = []
    today = date.today()
    for i in range(7, -1, -1):
        week_start = today - timedelta(days=today.weekday() + i * 7)
        week_end = week_start + timedelta(days=6)
        count = all_apps.filter(
            data_aplicacao__gte=week_start,
            data_aplicacao__lte=week_end,
        ).count()
        weeks_labels.append(week_start.strftime('%b %d'))
        weeks_data.append(count)

    # Kanban data
    kanban_columns = []
    for status_val, status_label in JobApplication.STATUS_CHOICES:
        col_qs = JobApplication.objects.filter(user=request.user, status=status_val)
        kanban_columns.append({
            'status': status_val,
            'label': status_label,
            'color': JobApplication.STATUS_COLORS.get(status_val, 'bg-gray-700 text-gray-300'),
            'apps': col_qs,
            'count': col_qs.count(),
        })

    return render(request, 'job_tracker/tracker.html', {
        'applications': qs,
        'status_filter': status_filter,
        'status_choices': JobApplication.STATUS_CHOICES,
        'total': total,
        'in_progress': in_progress,
        'offers': offers,
        'response_rate': response_rate,
        'weeks_labels': json.dumps(weeks_labels),
        'weeks_data': json.dumps(weeks_data),
        'kanban_columns': kanban_columns,
        'pipeline_stages': JobApplication.PIPELINE_STAGES,
        'negative_stages': JobApplication.NEGATIVE_STAGES,
    })


@login_required
def tracker_add(request):
    """Create a new tracked application."""
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, f'"{app.job_title} @ {app.company}" added to tracker.')
            if request.headers.get('HX-Request'):
                return JsonResponse({'ok': True, 'redirect': '/tracker/'})
            return redirect('job_tracker:list')
    else:
        form = JobApplicationForm()

    if request.headers.get('HX-Request'):
        return render(request, 'job_tracker/partials/add_form.html', {'form': form})
    return render(request, 'job_tracker/tracker.html', {'add_form': form, 'show_add_modal': True})


@login_required
def tracker_detail(request, pk):
    """Slide-over detail panel (HTMX partial)."""
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    status_form = StatusUpdateForm(instance=app)
    status_labels = dict(JobApplication.STATUS_CHOICES)
    pipeline_stages_data = [
        {
            'value': s,
            'label': status_labels[s],
            'color': JobApplication.STATUS_COLORS.get(s, 'bg-gray-700 text-gray-300'),
        }
        for s in JobApplication.PIPELINE_STAGES
    ]
    return render(request, 'job_tracker/partials/detail.html', {
        'app': app,
        'status_form': status_form,
        'pipeline_stages_data': pipeline_stages_data,
        'negative_stages': JobApplication.NEGATIVE_STAGES,
    })


@login_required
@require_http_methods(['POST'])
def tracker_update_status(request, pk):
    """HTMX: update status (and notes) inline."""
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    new_status = request.POST.get('status')
    notas = request.POST.get('notas', app.notas)
    if new_status and new_status in dict(JobApplication.STATUS_CHOICES):
        app.status = new_status
        app.notas = notas
        app.save(update_fields=['status', 'notas', 'data_atualizacao'])
    if request.headers.get('HX-Request'):
        return render(request, 'job_tracker/partials/status_badge.html', {'app': app})
    return redirect('job_tracker:list')


@login_required
def tracker_edit(request, pk):
    """Full edit view."""
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated.')
            return redirect('job_tracker:list')
    else:
        form = JobApplicationForm(instance=app)
    return render(request, 'job_tracker/edit.html', {'form': form, 'app': app})


@login_required
@require_http_methods(['POST'])
def tracker_delete(request, pk):
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    app.delete()
    messages.success(request, 'Application removed from tracker.')
    return redirect('job_tracker:list')


@login_required
@require_http_methods(['POST'])
def tracker_kanban_move(request):
    """HTMX/JSON endpoint: drag-and-drop status update."""
    data = json.loads(request.body)
    app = get_object_or_404(JobApplication, pk=data['id'], user=request.user)
    new_status = data.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        app.status = new_status
        app.save(update_fields=['status', 'data_atualizacao'])
    return JsonResponse({'ok': True})
