from django.urls import path
from . import views

app_name = 'cv_adapter'

urlpatterns = [
    path('upload/', views.upload_cv, name='upload_cv'),
    path('adapt/', views.adapt_cv_view, name='adapt'),
    path('adapt/process/', views.process_adaptation, name='process'),
    path('result/<int:pk>/', views.result_view, name='result'),
    path('result/<int:pk>/download/', views.download_docx, name='download_docx'),
    path('history/', views.history_view, name='history'),
]
