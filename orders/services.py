from django.db import transaction
from django.core.mail import send_mail
from .models import Order, OrderItem, ShippingAddress
from cart.cart import get_or_create_cart


@transaction.atomic
def create_order(request, data):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        raise ValueError('Cart is empty.')

    # Validate stock
    for item in cart.items.select_related('product'):
        if item.quantity > item.product.stock:
            raise ValueError(f"Insufficient stock for {item.product.name}")

    order = Order.objects.create(user=request.user)

    total = 0
    for item in cart.items.select_related('product'):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=item.product.price,
        )
        total += item.product.price * item.quantity

        # Deduct stock atomically
        item.product.stock -= item.quantity
        item.product.save()

    order.total_amount = total
    order.save()

    ShippingAddress.objects.create(
        order=order,
        full_name=data['full_name'],
        phone=data['phone'],
        address=data['address'],
        city=data['city'],
    )

    # Clear cart
    cart.items.all().delete()

    # Send confirmation email (console backend in dev)
    try:
        send_mail(
            subject=f'Order {order.order_number} Confirmed',
            message=f'Thank you! Your order total is ${order.total_amount}.',
            from_email='noreply@shopease.local',
            recipient_list=[request.user.email],
            fail_silently=True,
        )
    except Exception:
        pass

    return order