from django.contrib import admin
from .models import JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company', 'user', 'status', 'data_aplicacao')
    list_filter = ('status',)
    search_fields = ('job_title', 'company', 'user__email')
    raw_id_fields = ('cv_adaptation',)
