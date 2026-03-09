import os
from django.db import models
from django.conf import settings


def cv_upload_path(instance, filename):
    return os.path.join('cvs', str(instance.user.id), filename)


class CVBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cv_bases',
    )
    file = models.FileField(upload_to=cv_upload_path, blank=True, null=True)
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CV Base'
        verbose_name_plural = 'CV Bases'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.original_filename}"

    @property
    def file_extension(self):
        _, ext = os.path.splitext(self.original_filename)
        return ext.lower()


class JobApplication(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_applications',
    )
    cv_base = models.ForeignKey(
        CVBase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
    )
    job_title = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    job_description = models.TextField()

    # AI-generated output
    cv_adapted = models.TextField(blank=True)
    cover_letter = models.TextField(blank=True)
    linkedin_message = models.CharField(max_length=500, blank=True)
    keywords_found = models.JSONField(default=list, blank=True)
    keywords_missing = models.JSONField(default=list, blank=True)
    suggestions = models.JSONField(default=list, blank=True)
    score_match = models.IntegerField(default=0)

    # Processing state
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_DONE, 'Done'),
        (STATUS_ERROR, 'Error'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Application'
        verbose_name_plural = 'Job Applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.job_title or 'Untitled'} ({self.created_at.date()})"
