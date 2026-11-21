from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category


def home(request):
    featured = Product.objects.filter(is_active=True).select_related('category')[:12]
    categories = Category.objects.all()
    return render(request, 'home.html', {'featured': featured, 'categories': categories})


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category_slug:
        products = products.filter(category__slug=category_slug)

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'store/product_list.html', {
        'querystring': params.urlencode(),
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {'product': product, 'related': related})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(is_active=True)
    return render(request, 'store/category_detail.html', {'category': category, 'products': products})


def product_search(request):
    return product_list(request)