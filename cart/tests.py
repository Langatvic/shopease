from django.test import TestCase
from store.models import Category, Product
from .cart import add_to_cart, get_or_create_cart


class CartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Cat')
        self.product = Product.objects.create(
            category=self.category, name='Test Prod', price=10, stock=5
        )

    def test_add_to_cart(self):
        request = self.client.request().wsgi_request
        request.session = self.client.session
        add_to_cart(request, self.product.id, 2)
        cart = get_or_create_cart(request)
        self.assertEqual(cart.count, 2)