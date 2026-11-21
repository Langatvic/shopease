from .models import Cart, CartItem
from store.models import Product


def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key,
                                             user__isnull=True)
    return cart


def add_to_cart(request, product_id, quantity=1):
    cart = get_or_create_cart(request)
    product = Product.objects.get(id=product_id)
    quantity = max(1, int(quantity))
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    if item.quantity > product.stock:
        item.quantity = product.stock
    item.save()
    return item


def remove_from_cart(request, product_id):
    cart = get_or_create_cart(request)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()


def update_cart_item(request, product_id, quantity):
    cart = get_or_create_cart(request)
    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
        quantity = int(quantity)
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = min(quantity, item.product.stock)
            item.save()
    except CartItem.DoesNotExist:
        pass


def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()


def merge_session_cart(request, user):
    """Merge anonymous cart into user cart after login."""
    if request.session.session_key:
        try:
            session_cart = Cart.objects.get(session_key=request.session.session_key, user__isnull=True)
        except Cart.DoesNotExist:
            return
        user_cart, _ = Cart.objects.get_or_create(user=user)
        for item in session_cart.items.all():
            existing, created = CartItem.objects.get_or_create(
                cart=user_cart, product=item.product,
                defaults={'quantity': item.quantity}
            )
            if not created:
                existing.quantity += item.quantity
                existing.save()
        session_cart.delete()