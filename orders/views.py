from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import customer_required
from django.contrib import messages
from .forms import CheckoutForm
from .services import create_order, deduct_order_stock
from .models import Order
from cart.cart import get_or_create_cart
from payments.services import record_payment



@customer_required
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
                method = form.cleaned_data['payment_method']

                record_payment(order, method=method)

                # M-Pesa: wait for successful callback before deducting stock.
                if method == 'mpesa':
                    messages.success(
                        request,
                        f'Order {order.order_number} placed. Now pay with M-Pesa.'
                    )
                    return redirect(
                        'payments:mpesa_stkpush',
                        order_number=order.order_number
                    )

                # Cash on Delivery: deduct stock when order is accepted.
                deduct_order_stock(order)

                order.status = 'confirmed'
                order.save(update_fields=['status', 'updated_at'])

                messages.success(
                    request,
                    f'Order {order.order_number} placed successfully!'
                )

                return redirect(
                    'orders:order_detail',
                    order_number=order.order_number
                )

            except ValueError as e:
                messages.error(request, str(e))

    else:
        form = CheckoutForm(initial={
            'full_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.phone,
            'address': request.user.address,
            'city': request.user.city,
        })

    return render(
        request,
        'orders/checkout.html',
        {'form': form, 'cart': cart}
    )



@customer_required
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_history.html', {'orders': orders})


@customer_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )
    return render(request, 'orders/order_detail.html', {'order': order})


@customer_required
def order_success(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )
    return render(request, 'orders/order_success.html', {'order': order})