import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import apps.cv_adapter.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CVBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=apps.cv_adapter.models.cv_upload_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('extracted_text', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cv_bases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'CV Base',
                'verbose_name_plural': 'CV Bases',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_title', models.CharField(blank=True, max_length=255)),
                ('company_name', models.CharField(blank=True, max_length=255)),
                ('job_description', models.TextField()),
                ('cv_adapted', models.TextField(blank=True)),
                ('cover_letter', models.TextField(blank=True)),
                ('keywords_found', models.JSONField(blank=True, default=list)),
                ('keywords_missing', models.JSONField(blank=True, default=list)),
                ('suggestions', models.JSONField(blank=True, default=list)),
                ('score_match', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('done', 'Done'), ('error', 'Error')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cv_base', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applications', to='cv_adapter.cvbase')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_applications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Job Application',
                'verbose_name_plural': 'Job Applications',
                'ordering': ['-created_at'],
            },
        ),
    ]
