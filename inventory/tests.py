from django.test import TestCase
from .services import restock, deduct_stock
from store.models import Category, Product


class InventoryTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='Cat')
        self.product = Product.objects.create(category=cat, name='P', price=10, stock=5)

    def test_restock(self):
        restock(self.product, 10)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 15)

    def test_deduct_stock(self):
        deduct_stock(self.product, 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 2)