from django.db import transaction
from .models import StockLog, InventoryAlert


def restock(product, quantity, reason='Manual restock'):
    with transaction.atomic():
        product.stock += quantity
        product.save()
        StockLog.objects.create(product=product, change_type='in',
                                quantity=quantity, reason=reason)


def deduct_stock(product, quantity, reason='Order placed'):
    with transaction.atomic():
        if quantity > product.stock:
            raise ValueError(f'Insufficient stock for {product.name}')
        product.stock -= quantity
        product.save()
        StockLog.objects.create(product=product, change_type='out',
                                quantity=quantity, reason=reason)
        if product.stock <= 5:
            InventoryAlert.objects.get_or_create(product=product)


def check_availability(product, quantity):
    return product.stock >= quantity