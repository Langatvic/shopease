from django.core.cache import cache
from django.db import transaction
from orders.services import deduct_order_stock

from . import mpesa
from .models import Payment


def record_payment(order, method='cod', status='pending', transaction_ref=''):
    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={'amount': order.total_amount, 'method': method, 'status': status,
                  'transaction_ref': transaction_ref}
    )
    if not created and payment.status != 'paid' and payment.method != method:
        payment.method = method
        payment.save(update_fields=['method'])
    return payment


@transaction.atomic
def mark_paid(payment, transaction_ref=''):
    payment = Payment.objects.select_for_update().select_related('order').get(
        pk=payment.pk
    )

    if payment.status == 'paid':
        return payment

    order = payment.order

    if order.status == 'cancelled':
        raise ValueError('Cannot complete payment for a cancelled order.')

    # Deduct stock exactly once.
    deduct_order_stock(order)

    payment.status = 'paid'

    if transaction_ref:
        payment.transaction_ref = transaction_ref

    payment.save(update_fields=['status', 'transaction_ref'])

    order.status = 'confirmed'
    order.save(update_fields=['status', 'updated_at'])

    return payment


def start_mpesa_payment(order, phone):
    """Send the PIN prompt. Raises mpesa.MpesaError with a customer-safe message on failure."""
    payment = record_payment(order, method='mpesa')
    if payment.status == 'paid':
        return payment
    result = mpesa.stk_push(phone, payment.amount, reference=order.order_number)
    payment.method = 'mpesa'
    payment.status = 'pending'
    payment.phone = mpesa.normalize_phone(phone)
    payment.checkout_request_id = result['checkout_request_id']
    payment.merchant_request_id = result['merchant_request_id']
    payment.result_desc = ''
    payment.save()
    return payment


def apply_result(payment, result_code, result_desc, receipt=''):
    """Record a finished transaction. Safe to call more than once for the same payment."""
    if payment.status == 'paid':
        if receipt and not payment.transaction_ref:
            payment.transaction_ref = receipt
            payment.save(update_fields=['transaction_ref'])
        return payment
    if result_code == 0:
        payment.result_desc = result_desc
        mark_paid(payment, receipt)
    else:
        payment.status = 'failed'
        payment.result_desc = result_desc[:255]
        payment.save()
    return payment


@transaction.atomic
def handle_callback(payload):
    """Process Safaricom's callback. Returns True if it matched one of our payments."""
    data = mpesa.parse_callback(payload)
    if not data:
        return False
    payment = (Payment.objects.select_for_update().select_related('order')
               .filter(checkout_request_id=data['checkout_request_id'], method='mpesa').first())
    if not payment:
        return False
    if data['result_code'] == 0:
        # Never trust a "success" that does not match what we asked for.
        if data['amount'] is None or mpesa.amount_to_kes(data['amount']) < mpesa.amount_to_kes(payment.amount):
            payment.status = 'failed'
            payment.result_desc = 'Amount paid did not match the order total.'
            payment.transaction_ref = data['receipt']
            payment.save()
            return True
    apply_result(payment, data['result_code'], data['result_desc'], data['receipt'])
    return True


def refresh_from_daraja(payment):
    """
    Fallback for when the callback cannot reach us (e.g. local development): ask Daraja directly.
    Throttled so a polling page cannot hammer the API.
    """
    if payment.status != 'pending' or not payment.checkout_request_id:
        return payment
    if not cache.add(f'mpesa-query-{payment.pk}', 1, 10):
        return payment
    try:
        result = mpesa.stk_query(payment.checkout_request_id)
    except mpesa.MpesaError:
        return payment
    if result:
        with transaction.atomic():
            locked = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
            apply_result(locked, result['result_code'], result['result_desc'])
            return locked
    return payment
