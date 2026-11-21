from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .services import record_payment


@login_required
def payment_method(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        method = request.POST.get('method', 'cod')
        record_payment(order, method=method)
        messages.success(request, 'Payment method selected.')
        return redirect('orders:order_detail', order_number=order.order_number)
    return render(request, 'payments/payment_method.html', {'order': order})


@login_required
def cod_confirm(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'payments/cod_confirm.html', {'order': order})


@login_required
def mpesa_stkpush(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'payments/mpesa_stkpush.html', {'order': order})