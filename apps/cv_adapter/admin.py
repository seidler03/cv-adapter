from django.contrib import admin
from .models import CVBase, JobApplication


@admin.register(CVBase)
class CVBaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'created_at')
    search_fields = ('user__email', 'original_filename')
    readonly_fields = ('extracted_text',)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company_name', 'score_match', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__email', 'job_title', 'company_name')
    readonly_fields = ('cv_adapted', 'cover_letter', 'keywords_found',
                       'keywords_missing', 'suggestions')
