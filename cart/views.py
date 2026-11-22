
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import shopping_access_required

from .cart import (
    get_or_create_cart,
    add_to_cart,
    remove_from_cart,
    update_cart_item,
    clear_cart,
)


@shopping_access_required
def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product')

    return render(
        request,
        'cart/cart_detail.html',
        {'cart': cart, 'items': items}
    )


@shopping_access_required
@require_POST
def cart_add(request, product_id):
    quantity = request.POST.get('quantity', 1)
    add_to_cart(request, product_id, quantity)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({'success': True, 'count': cart.count})

    return redirect('cart:detail')


@shopping_access_required
@require_POST
def cart_update(request, product_id):
    quantity = request.POST.get('quantity', 1)
    update_cart_item(request, product_id, quantity)
    return redirect('cart:detail')


@shopping_access_required
@require_POST
def cart_remove(request, product_id):
    remove_from_cart(request, product_id)
    return redirect('cart:detail')


@shopping_access_required
@require_POST
def cart_clear(request):
    clear_cart(request)
    return redirect('cart:detail')


@shopping_access_required
def cart_summary(request):
    cart = get_or_create_cart(request)

    return render(
        request,
        'cart/cart_summary.html',
        {'cart': cart}
    )
