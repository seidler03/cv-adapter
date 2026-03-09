import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from .forms import CVUploadForm, CVPasteForm, JobApplicationForm
from .models import CVBase, JobApplication
from .parsers import extract_text
from .ai_service import adapt_cv
from .docx_generator import build_docx

logger = logging.getLogger(__name__)


@login_required
def upload_cv(request):
    """Upload a base CV and extract its text, or paste CV text directly."""
    if request.method == 'POST':
        mode = request.POST.get('input_mode', 'file')

        # ── Paste mode: user typed/pasted text ──────────────────────────────
        if mode == 'paste':
            paste_form = CVPasteForm(request.POST)
            if paste_form.is_valid():
                CVBase.objects.create(
                    user=request.user,
                    file=None,
                    original_filename=paste_form.cleaned_data['cv_name'],
                    extracted_text=paste_form.cleaned_data['pasted_text'],
                )
                messages.success(request, f'"{paste_form.cleaned_data["cv_name"]}" saved successfully.')
                return redirect('dashboard:index')
            return render(request, 'cv_adapter/upload_cv.html', {
                'form': CVUploadForm(),
                'paste_form': paste_form,
                'show_paste': True,
            })

        # ── File upload mode ────────────────────────────────────────────────
        form = CVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            filename = request.FILES['file'].name
            try:
                request.FILES['file'].seek(0)
                extracted = extract_text(request.FILES['file'], filename)
            except Exception as exc:
                logger.warning('CV text extraction failed for "%s": %s', filename, exc)
                # Don't save — ask user to paste the text instead
                return render(request, 'cv_adapter/upload_cv.html', {
                    'form': CVUploadForm(),
                    'paste_form': CVPasteForm(initial={'cv_name': filename.rsplit('.', 1)[0]}),
                    'show_paste': True,
                    'extraction_error': (
                        f'Could not read text from “{filename}” — it may be a scanned or image-only PDF. '
                        f'Please paste your CV text below instead.'
                    ),
                })

            if not extracted.strip():
                return render(request, 'cv_adapter/upload_cv.html', {
                    'form': CVUploadForm(),
                    'paste_form': CVPasteForm(initial={'cv_name': filename.rsplit('.', 1)[0]}),
                    'show_paste': True,
                    'extraction_error': (
                        f'“{filename}” appears to have no readable text (possibly a scanned PDF). '
                        f'Please paste your CV text below instead.'
                    ),
                })

            cv = form.save(commit=False)
            cv.user = request.user
            cv.original_filename = filename
            cv.extracted_text = extracted
            cv.save()
            messages.success(request, f'"{filename}" uploaded and parsed successfully.')
            return redirect('dashboard:index')

    else:
        form = CVUploadForm()
    return render(request, 'cv_adapter/upload_cv.html', {
        'form': form,
        'paste_form': CVPasteForm(),
        'show_paste': False,
    })


@login_required
def adapt_cv_view(request):
    """Main page: select CV + paste JD, then submit via HTMX."""
    from django.conf import settings
    from django.utils import timezone
    form = JobApplicationForm(user=request.user)
    cv_bases = CVBase.objects.filter(user=request.user)
    user = request.user
    now = timezone.now()
    monthly_usage = JobApplication.objects.filter(
        user=user, created_at__year=now.year, created_at__month=now.month,
    ).count()
    is_pro = getattr(user, 'is_pro', False) or (
        hasattr(user, 'subscription') and user.subscription.is_active
    )
    return render(request, 'cv_adapter/adapt.html', {
        'form': form,
        'cv_bases': cv_bases,
        'is_pro': is_pro,
        'monthly_usage': monthly_usage,
        'monthly_limit': settings.FREE_PLAN_MONTHLY_LIMIT,
    })


@login_required
@require_POST
def process_adaptation(request):
    """
    HTMX endpoint: run the AI adaptation and return a partial HTML fragment.
    The UsageLimitMiddleware already checked the quota before reaching here.
    """
    form = JobApplicationForm(request.user, request.POST)
    if not form.is_valid():
        if request.headers.get('HX-Request'):
            return render(request, 'cv_adapter/partials/error.html', {
                'errors': form.errors,
            }, status=400)
        messages.error(request, 'Please correct the errors below.')
        return redirect('cv_adapter:adapt')

    job_app = form.save(commit=False)
    job_app.user = request.user
    job_app.status = JobApplication.STATUS_PROCESSING
    job_app.save()

    cv_text = job_app.cv_base.extracted_text if job_app.cv_base else ''

    if not cv_text.strip():
        # Delete the unsaved stub and return an error — no point calling the AI
        job_app.delete()
        error_msg = (
            'The selected CV has no readable text. '
            'Please re-upload it as a text-based PDF/DOCX, or use the "Paste text" option '
            'on the Upload CV page to add your CV content manually.'
        )
        if request.headers.get('HX-Request'):
            return render(request, 'cv_adapter/partials/error.html', {
                'message': error_msg,
            }, status=422)
        messages.error(request, error_msg)
        return redirect('cv_adapter:adapt')

    try:
        result = adapt_cv(cv_text, job_app.job_description)
    except Exception as exc:
        logger.error('AI adaptation failed for application %s: %s', job_app.pk, exc)
        job_app.status = JobApplication.STATUS_ERROR
        job_app.error_message = str(exc)
        job_app.save(update_fields=['status', 'error_message'])

        if request.headers.get('HX-Request'):
            return render(request, 'cv_adapter/partials/error.html', {
                'message': f'AI error: {exc}',
            }, status=500)
        messages.error(request, f'AI processing failed: {exc}')
        return redirect('cv_adapter:adapt')

    job_app.cv_adapted = result.get('cv_adaptado', '')
    job_app.cover_letter = result.get('cover_letter', '')
    job_app.linkedin_message = result.get('linkedin_message', '')[:500]
    job_app.keywords_found = result.get('keywords_encontradas', [])
    job_app.keywords_missing = result.get('keywords_faltando', [])
    job_app.suggestions = result.get('sugestoes', [])
    job_app.score_match = result.get('score', 0)
    job_app.job_title = result.get('cargo_identificado', '') or ''
    job_app.company_name = result.get('empresa_identificada', '') or ''
    job_app.status = JobApplication.STATUS_DONE
    job_app.save()

    # Auto-create a tracker entry so the application appears in Job Tracker
    try:
        from apps.job_tracker.models import JobApplication as TrackerApp
        TrackerApp.objects.create(
            user=request.user,
            job_title=job_app.job_title or 'Não identificado',
            company=job_app.company_name or 'Não identificado',
            job_description=job_app.job_description,
            cv_adaptation=job_app,
            status='applied',
        )
    except Exception as tracker_exc:
        logger.warning('Could not auto-create tracker entry: %s', tracker_exc)

    if request.headers.get('HX-Request'):
        return render(request, 'cv_adapter/partials/result.html', {
            'application': job_app,
        })
    return redirect('cv_adapter:result', pk=job_app.pk)


@login_required
def result_view(request, pk):
    """Full-page result view for a specific adaptation."""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    return render(request, 'cv_adapter/result.html', {'application': application})


@login_required
def download_docx(request, pk):
    """Generate and stream a DOCX file for the adapted CV."""
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if not application.cv_adapted:
        messages.error(request, 'No adapted CV available for this application.')
        return redirect('cv_adapter:result', pk=pk)

    docx_bytes = build_docx(application.cv_adapted, title='Adapted CV')
    filename = f"CV_adapted_{application.pk}.docx"
    response = HttpResponse(
        docx_bytes,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def history_view(request):
    """List all past adaptations for the logged-in user."""
    applications = JobApplication.objects.filter(
        user=request.user, status=JobApplication.STATUS_DONE
    ).select_related('cv_base')
    return render(request, 'cv_adapter/history.html', {'applications': applications})
