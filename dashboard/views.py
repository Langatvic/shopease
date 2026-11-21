from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from store.models import Product, Category
from store.forms import ProductForm, CategoryForm
from orders.models import Order
from accounts.models import CustomUser
from .decorators import admin_required


@admin_required
def index(request):
    data = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'total_customers': CustomUser.objects.filter(role='customer').count(),
        'revenue': Order.objects.filter(status__in=['delivered', 'shipped']).aggregate(
            total=Sum('total_amount'))['total'] or 0,
        'recent_orders': Order.objects.order_by('-created_at')[:5],
        'low_stock': Product.objects.filter(stock__lt=5).order_by('stock')[:5],
    }
    return render(request, 'dashboard/index.html', data)


# ----- Products -----
@admin_required
def product_list(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'dashboard/products/product_list.html', {'products': products})


@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created.')
            return redirect('dashboard:product_list')
    else:
        form = ProductForm()
    return render(request, 'dashboard/products/product_form.html', {'form': form, 'action': 'Create'})


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            return redirect('dashboard:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/products/product_form.html', {'form': form, 'action': 'Edit', 'product': product})


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('dashboard:product_list')
    return render(request, 'dashboard/products/product_confirm_delete.html', {'product': product})


# ----- Categories -----
@admin_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/categories/category_list.html', {'categories': categories})


# ----- Orders -----
@admin_required
def order_list(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    return render(request, 'dashboard/orders/order_list.html', {'orders': orders})


@admin_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'dashboard/orders/order_detail.html', {'order': order})


@admin_required
def order_status_update(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order {order.order_number} updated to {new_status}.')
            return redirect('dashboard:order_detail', order_number=order.order_number)
    return render(request, 'dashboard/orders/order_status_update.html', {'order': order})


# ----- Customers -----
@admin_required
def customer_list(request):
    customers = CustomUser.objects.filter(role='customer').annotate(
        order_count=Count('orders'))
    return render(request, 'dashboard/customers/customer_list.html', {'customers': customers})