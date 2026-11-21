from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from store.models import Product
from .forms import RestockForm
from .services import restock
from .models import StockLog, InventoryAlert


@staff_member_required
def stock_list(request):
    products = Product.objects.all().order_by('stock')
    alerts = InventoryAlert.objects.filter(is_resolved=False)
    return render(request, 'inventory/stock_list.html',
                  {'products': products, 'alerts': alerts})


@staff_member_required
def stock_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = RestockForm(request.POST)
        if form.is_valid():
            restock(product, form.cleaned_data['quantity'], form.cleaned_data['reason'])
            messages.success(request, f'Stock updated for {product.name}.')
            return redirect('inventory:stock_list')
    else:
        form = RestockForm()
    return render(request, 'inventory/stock_update.html', {'product': product, 'form': form})


@staff_member_required
def stock_log(request):
    logs = StockLog.objects.select_related('product').all()
    return render(request, 'inventory/stock_log.html', {'logs': logs})