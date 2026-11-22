import json
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from orders.models import Order
from store.models import Category, Product
from . import mpesa
from .models import Payment
from .services import handle_callback, record_payment, start_mpesa_payment

MPESA = dict(MPESA_ENV='sandbox', MPESA_CONSUMER_KEY='k', MPESA_CONSUMER_SECRET='s', MPESA_SHORTCODE='174379',
             MPESA_PASSKEY='p', MPESA_CALLBACK_URL='https://example.test/payments/mpesa/callback/tok/',
             MPESA_CALLBACK_TOKEN='tok')


def callback_body(checkout_id, code=0, amount=100, receipt='QWE123ABC'):
    cb = {'MerchantRequestID': 'm1', 'CheckoutRequestID': checkout_id, 'ResultCode': code,
          'ResultDesc': 'The service request is processed successfully.' if code == 0 else 'Request cancelled by user'}
    if code == 0:
        cb['CallbackMetadata'] = {'Item': [
            {'Name': 'Amount', 'Value': amount}, {'Name': 'MpesaReceiptNumber', 'Value': receipt},
            {'Name': 'PhoneNumber', 'Value': 254712345678}]}
    return {'Body': {'stkCallback': cb}}


class HelperTests(TestCase):
    def test_normalize_phone(self):
        for raw in ('0712345678', '+254712345678', '254712345678', '712345678', '0712 345 678', '0112345678'):
            self.assertIsNotNone(mpesa.normalize_phone(raw), raw)
        self.assertEqual(mpesa.normalize_phone('0712 345 678'), '254712345678')
        for bad in ('', None, '12345', '0212345678', '25471234567', 'abc'):
            self.assertIsNone(mpesa.normalize_phone(bad), bad)

    def test_amount_rounds_up(self):
        self.assertEqual(mpesa.amount_to_kes(Decimal('99.01')), 100)
        self.assertEqual(mpesa.amount_to_kes(Decimal('100.00')), 100)


@override_settings(**MPESA)
class FlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('amina', 'a@example.com', 'pass12345')
        self.order = Order.objects.create(user=self.user, total_amount=Decimal('100.00'))
        self.client.force_login(self.user)

    def _start(self):
        with mock.patch('payments.mpesa.stk_push', return_value={
                'checkout_request_id': 'ws_CO_1', 'merchant_request_id': 'm1', 'message': 'ok'}):
            return start_mpesa_payment(self.order, '0712345678')

    def test_start_records_checkout_id(self):
        p = self._start()
        self.assertEqual((p.status, p.phone, p.checkout_request_id), ('pending', '254712345678', 'ws_CO_1'))

    def test_success_callback_marks_paid_and_confirms_order(self):
        self._start()
        self.assertTrue(handle_callback(callback_body('ws_CO_1')))
        p = Payment.objects.get(order=self.order)
        self.order.refresh_from_db()
        self.assertEqual((p.status, p.transaction_ref, self.order.status), ('paid', 'QWE123ABC', 'confirmed'))

    def test_callback_is_idempotent(self):
        self._start()
        handle_callback(callback_body('ws_CO_1'))
        handle_callback(callback_body('ws_CO_1', code=1032))   # late "cancelled" must not undo a paid order
        self.assertEqual(Payment.objects.get(order=self.order).status, 'paid')

    def test_cancelled_by_user_marks_failed(self):
        self._start()
        handle_callback(callback_body('ws_CO_1', code=1032))
        p = Payment.objects.get(order=self.order)
        self.assertEqual(p.status, 'failed')
        self.assertIn('cancelled', p.result_desc.lower())

    def test_underpayment_is_not_accepted(self):
        self._start()
        handle_callback(callback_body('ws_CO_1', amount=10))
        self.assertEqual(Payment.objects.get(order=self.order).status, 'failed')

    def test_unknown_checkout_id_ignored(self):
        self.assertFalse(handle_callback(callback_body('nope')))
        self.assertFalse(handle_callback({'garbage': True}))

    def test_callback_endpoint_requires_token(self):
        self._start()
        body = json.dumps(callback_body('ws_CO_1'))
        bad = self.client.post(reverse('payments:mpesa_callback', args=['wrong']), body, content_type='application/json')
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(Payment.objects.get(order=self.order).status, 'pending')
        ok = self.client.post(reverse('payments:mpesa_callback', args=['tok']), body, content_type='application/json')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(Payment.objects.get(order=self.order).status, 'paid')

    def test_stk_page_rejects_bad_phone(self):
        r = self.client.post(reverse('payments:mpesa_stkpush', args=[self.order.order_number]), {'phone': '123'}, follow=True)
        self.assertContains(r, 'valid Safaricom number')
        self.assertFalse(Payment.objects.filter(order=self.order, checkout_request_id__gt='').exists())

    def test_status_endpoint_is_owner_only(self):
        self._start()
        other = get_user_model().objects.create_user('other', 'o@example.com', 'pass12345')
        self.client.force_login(other)
        r = self.client.get(reverse('payments:mpesa_status', args=[self.order.order_number]))
        self.assertEqual(r.status_code, 404)

    @override_settings(MPESA_CONSUMER_KEY='')
    def test_missing_config_gives_friendly_error(self):
        with self.assertRaises(mpesa.MpesaError):
            mpesa.stk_push('0712345678', 100, 'REF')
