from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def log_order_status_change(sender, instance, created, **kwargs):
    if not created:
        # In production, log to a file or service
        print(f"[Order] {instance.order_number} → {instance.status}")