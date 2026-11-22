import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist

from orders.models import Order
from . import mpesa
from .models import Payment
from .services import handle_callback, record_payment, refresh_from_daraja, start_mpesa_payment

log = logging.getLogger(__name__)


def _own_order(request, order_number):
    return get_object_or_404(Order, order_number=order_number, user=request.user)


@login_required
def payment_method(request, order_number):
    order = _own_order(request, order_number)
    if request.method == 'POST':
        method = request.POST.get('method', 'cod')
        if method not in ('cod', 'mpesa'):
            method = 'cod'
        record_payment(order, method=method)
        if method == 'mpesa':
            return redirect('payments:mpesa_stkpush', order_number=order.order_number)
        messages.success(request, 'Payment method selected.')
        return redirect('orders:order_detail', order_number=order.order_number)
    return render(request, 'payments/payment_method.html', {'order': order})


@login_required
def cod_confirm(request, order_number):
    order = _own_order(request, order_number)
    return render(request, 'payments/cod_confirm.html', {'order': order})


@login_required
def mpesa_stkpush(request, order_number):
    order = _own_order(request, order_number)
    payment = Payment.objects.filter(order=order).first()

    if request.method == 'POST':
        if order.status == 'cancelled':
            messages.error(request, 'This order was cancelled.')
        elif payment and payment.status == 'paid':
            return redirect('orders:order_detail', order_number=order.order_number)
        else:
            try:
                start_mpesa_payment(order, request.POST.get('phone', ''))
                messages.success(request, 'Check your phone and enter your M-Pesa PIN.')
            except mpesa.MpesaError as exc:
                messages.error(request, str(exc))
        return redirect('payments:mpesa_stkpush', order_number=order.order_number)


    try:
            shipping_phone = order.shipping.phone
    except ObjectDoesNotExist:
            shipping_phone = ''

    phone = (payment.phone if payment and payment.phone else '') or shipping_phone
    return render(request, 'payments/mpesa_stkpush.html', {'order': order, 'payment': payment, 'phone': phone})


@login_required
def mpesa_status(request, order_number):
    """Polled by the payment page while it waits for the customer to enter their PIN."""
    order = _own_order(request, order_number)
    payment = get_object_or_404(Payment, order=order)
    payment = refresh_from_daraja(payment)
    return JsonResponse({
        'status': payment.status,
        'message': payment.result_desc,
        'receipt': payment.transaction_ref,
        'order_url': reverse('orders:order_detail', args=[order.order_number]),
    })


@csrf_exempt
@require_POST
def mpesa_callback(request, token):
    """Called by Safaricom (not by a browser). The secret token in the URL keeps strangers out."""
    expected = getattr(settings, 'MPESA_CALLBACK_TOKEN', '')
    if not expected or token != expected:
        return HttpResponseForbidden()
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        return HttpResponse(status=400)
    if not handle_callback(payload):
        log.warning('M-Pesa callback did not match a payment: %s', request.body[:500])
    # Always acknowledge so Safaricom does not keep retrying.
    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
