
from django.db import transaction
from django.core.mail import send_mail
from .models import Order, OrderItem, ShippingAddress
from cart.cart import get_or_create_cart
from store.models import Product


@transaction.atomic
def create_order(request, data):
    cart = get_or_create_cart(request)

    if not cart.items.exists():
        raise ValueError('Cart is empty.')

    # Check stock availability, but DO NOT deduct stock here.
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

    order.total_amount = total
    order.save(update_fields=['total_amount'])

    ShippingAddress.objects.create(
        order=order,
        full_name=data['full_name'],
        phone=data['phone'],
        address=data['address'],
        city=data['city'],
    )

    # Clear cart after successfully creating the order.
    cart.items.all().delete()

    try:
        send_mail(
            subject=f'Order {order.order_number} Received',
            message=(
                f'We received your order. '
                f'Order total: {order.total_amount}. '
                f'Your order will be processed according to its payment status.'
            ),
            from_email='noreply@shopease.local',
            recipient_list=[request.user.email],
            fail_silently=True,
        )
    except Exception:
        pass

    return order


@transaction.atomic
def deduct_order_stock(order):
    """
    Deduct inventory once for an order.
    Rechecks stock while locking product rows.
    """
    locked_order = Order.objects.select_for_update().get(pk=order.pk)

    if locked_order.stock_deducted:
        return locked_order

    items = locked_order.items.all()

    # First validate every item before changing any stock.
    products = []

    for item in items:
        if not item.product_id:
            raise ValueError(f'Product {item.product_name} is no longer available.')

        product = Product.objects.select_for_update().get(
            pk=item.product_id
        )

        if product.stock < item.quantity:
            raise ValueError(
                f'Insufficient stock for {item.product_name}. '
                f'Available: {product.stock}, requested: {item.quantity}.'
            )

        products.append((product, item.quantity))

    # Deduct stock only after all items have passed validation.
    for product, quantity in products:
        product.stock -= quantity
        product.save(update_fields=['stock'])

    locked_order.stock_deducted = True
    locked_order.save(update_fields=['stock_deducted'])

    return locked_order
