from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CheckoutForm
from .services import create_order
from .models import Order
from cart.cart import get_or_create_cart


@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:product_list')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = create_order(request, form.cleaned_data)
                messages.success(request, f'Order {order.order_number} placed successfully!')
                return redirect('orders:order_detail', order_number=order.order_number)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = CheckoutForm(initial={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.phone,
            'address': request.user.address,
            'city': request.user.city,
        })
    return render(request, 'orders/checkout.html', {'form': form, 'cart': cart})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('orders:order_history')
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})