from django.db import models
from orders.models import Order


class Payment(models.Model):
    METHODS = [('cod', 'Cash on Delivery'), ('mpesa', 'M-Pesa')]
    STATUS = [('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=10, choices=METHODS, default='cod')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS, default='pending')
    transaction_ref = models.CharField(max_length=100, blank=True)  # M-Pesa receipt number
    phone = models.CharField(max_length=15, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    result_desc = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.order.order_number}"
