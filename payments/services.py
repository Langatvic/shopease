from .models import Payment


def record_payment(order, method='cod', status='pending', transaction_ref=''):
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={'amount': order.total_amount, 'method': method, 'status': status,
                  'transaction_ref': transaction_ref}
    )
    return payment


def mark_paid(payment, transaction_ref=''):
    payment.status = 'paid'
    payment.transaction_ref = transaction_ref
    payment.save()