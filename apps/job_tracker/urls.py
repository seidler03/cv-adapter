from django.urls import path
from . import views

app_name = 'job_tracker'

urlpatterns = [
    path('', views.tracker_list, name='list'),
    path('add/', views.tracker_add, name='add'),
    path('<int:pk>/detail/', views.tracker_detail, name='detail'),
    path('<int:pk>/status/', views.tracker_update_status, name='update_status'),
    path('<int:pk>/edit/', views.tracker_edit, name='edit'),
    path('<int:pk>/delete/', views.tracker_delete, name='delete'),
    path('kanban/move/', views.tracker_kanban_move, name='kanban_move'),
]
