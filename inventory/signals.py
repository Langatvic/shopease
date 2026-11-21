from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import InventoryAlert


@receiver(post_save, sender=InventoryAlert)
def notify_low_stock(sender, instance, created, **kwargs):
    if created:
        print(f"[ALERT] Low stock: {instance.product.name}")