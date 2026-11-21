from .models import Cart


def cart(request):
    if request.user.is_authenticated:
        cart_obj = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart_obj = Cart.objects.filter(session_key=request.session.session_key,
                                       user__isnull=True).first()
    else:
        cart_obj = None
    return {'cart': cart_obj}