from django.test import TestCase
from .models import Category, Product


class StoreTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category, name='Phone', price=199.99, stock=10
        )

    def test_product_slug(self):
        self.assertEqual(self.product.slug, 'phone')

    def test_product_list(self):
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone')