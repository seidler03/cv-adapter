from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('cv/', include('apps.cv_adapter.urls')),
    path('payments/', include('apps.payments.urls')),
    path('tracker/', include('apps.job_tracker.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
