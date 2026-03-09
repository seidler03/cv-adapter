from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('upgrade/', views.upgrade_page, name='upgrade'),
    path('checkout/', views.create_checkout_session, name='checkout'),
    path('success/', views.checkout_success, name='success'),
    path('cancel/', views.cancel_subscription, name='cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
]
