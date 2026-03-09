from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Subscription


@receiver(post_save, sender=User)
def create_subscription(sender, instance, created, **kwargs):
    """Automatically create a free subscription for every new user."""
    if created:
        Subscription.objects.get_or_create(user=instance)
