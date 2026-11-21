from django.db import models
from store.models import Product


class StockLog(models.Model):
    CHANGE_TYPES = [('in', 'Stock In'), ('out', 'Stock Out')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_logs')
    change_type = models.CharField(max_length=3, choices=CHANGE_TYPES)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.product.name} {self.change_type} {self.quantity}"


class InventoryAlert(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    threshold = models.PositiveIntegerField(default=5)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.product.name}"