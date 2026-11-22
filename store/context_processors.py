from .models import Category


def nav_categories(request):
    """Categories for the header's second row, available on every page."""
    return {'nav_categories': Category.objects.all()[:8]}
