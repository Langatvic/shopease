from django.test import TestCase
from django.urls import reverse
from .models import CustomUser


class AccountsTests(TestCase):
    def test_registration(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Str0ngPass!123',
            'password2': 'Str0ngPass!123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username='testuser').exists())