"""
Safaricom Daraja (M-Pesa Express / STK Push) client.

Settings used (all read from .env through shopease/settings.py):
    MPESA_ENV, MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE,
    MPESA_PASSKEY, MPESA_CALLBACK_URL, MPESA_TRANSACTION_TYPE
"""
import base64
import logging
import re
import time
from datetime import datetime
from decimal import Decimal, ROUND_CEILING

import requests
from django.conf import settings

log = logging.getLogger(__name__)

BASE_URLS = {
    'sandbox': 'https://sandbox.safaricom.co.ke',
    'production': 'https://api.safaricom.co.ke',
}
TIMEOUT = 20  # seconds

_token = {'value': None, 'expires': 0.0}


class MpesaError(Exception):
    """Raised for configuration or API problems; the message is safe to show to a customer."""


# ---------- helpers (no network) ----------

def normalize_phone(raw):
    """Return a Safaricom MSISDN as 2547XXXXXXXX / 2541XXXXXXXX, or None if it is not valid."""
    digits = re.sub(r'[\s\-().]', '', str(raw or ''))
    if digits.startswith('+'):
        digits = digits[1:]
    if re.fullmatch(r'0[17]\d{8}', digits):
        digits = '254' + digits[1:]
    elif re.fullmatch(r'[17]\d{8}', digits):
        digits = '254' + digits
    return digits if re.fullmatch(r'254[17]\d{8}', digits) else None


def amount_to_kes(amount):
    """M-Pesa only accepts whole shillings, so round up."""
    return int(Decimal(str(amount)).to_integral_value(rounding=ROUND_CEILING))


def parse_callback(payload):
    """
    Flatten Daraja's STK callback into a plain dict, or return None if the body is not one.
    Keys: checkout_request_id, merchant_request_id, result_code, result_desc,
          amount, receipt, phone (the last three only on success).
    """
    try:
        cb = payload['Body']['stkCallback']
        out = {
            'checkout_request_id': cb['CheckoutRequestID'],
            'merchant_request_id': cb.get('MerchantRequestID', ''),
            'result_code': int(cb['ResultCode']),
            'result_desc': cb.get('ResultDesc', ''),
            'amount': None, 'receipt': '', 'phone': '',
        }
    except (KeyError, TypeError, ValueError):
        return None
    items = (cb.get('CallbackMetadata') or {}).get('Item') or []
    meta = {i.get('Name'): i.get('Value') for i in items if isinstance(i, dict)}
    out['amount'] = meta.get('Amount')
    out['receipt'] = str(meta.get('MpesaReceiptNumber') or '')
    out['phone'] = str(meta.get('PhoneNumber') or '')
    return out


# ---------- Daraja calls ----------

def _conf():
    env = getattr(settings, 'MPESA_ENV', 'sandbox')
    conf = {
        'base': BASE_URLS.get(env, BASE_URLS['sandbox']),
        'key': getattr(settings, 'MPESA_CONSUMER_KEY', ''),
        'secret': getattr(settings, 'MPESA_CONSUMER_SECRET', ''),
        'shortcode': getattr(settings, 'MPESA_SHORTCODE', ''),
        'passkey': getattr(settings, 'MPESA_PASSKEY', ''),
        'callback': getattr(settings, 'MPESA_CALLBACK_URL', ''),
        'txn_type': getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline'),
    }
    missing = [k for k in ('key', 'secret', 'shortcode', 'passkey') if not conf[k]]
    if missing:
        log.error('M-Pesa not configured, missing: %s', ', '.join(missing))
        raise MpesaError('M-Pesa is not set up on this store yet. Please pay on delivery instead.')
    return conf


def _access_token(conf):
    if _token['value'] and _token['expires'] > time.time() + 30:
        return _token['value']
    try:
        r = requests.get(f"{conf['base']}/oauth/v1/generate", params={'grant_type': 'client_credentials'},
                         auth=(conf['key'], conf['secret']), timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        _token['value'] = data['access_token']
        _token['expires'] = time.time() + int(data.get('expires_in', 3599))
        return _token['value']
    except (requests.RequestException, KeyError, ValueError) as exc:
        log.error('Daraja token request failed: %s', exc)
        raise MpesaError('We could not reach M-Pesa. Please try again in a moment.')


def _password(conf):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{conf['shortcode']}{conf['passkey']}{ts}".encode()
    return base64.b64encode(raw).decode(), ts


def _post(conf, path, body):
    token = _access_token(conf)
    try:
        r = requests.post(f"{conf['base']}{path}", json=body, timeout=TIMEOUT,
                          headers={'Authorization': f'Bearer {token}'})
        try:
            data = r.json()
        except ValueError:
            data = {}
        return r.status_code, data
    except requests.RequestException as exc:
        log.error('Daraja request to %s failed: %s', path, exc)
        raise MpesaError('We could not reach M-Pesa. Please try again in a moment.')


def stk_push(phone, amount, reference, description='ShopEase order'):
    """
    Ask Safaricom to pop the PIN prompt on the customer's phone.
    Returns {'checkout_request_id', 'merchant_request_id', 'message'} or raises MpesaError.
    """
    msisdn = normalize_phone(phone)
    if not msisdn:
        raise MpesaError('Enter a valid Safaricom number, for example 0712 345 678.')
    conf = _conf()
    if not conf['callback'].startswith('https://'):
        log.error('MPESA_CALLBACK_URL must be a public https URL, got %r', conf['callback'])
        raise MpesaError('M-Pesa is not set up on this store yet. Please pay on delivery instead.')

    password, ts = _password(conf)
    status, data = _post(conf, '/mpesa/stkpush/v1/processrequest', {
        'BusinessShortCode': conf['shortcode'],
        'Password': password,
        'Timestamp': ts,
        'TransactionType': conf['txn_type'],
        'Amount': amount_to_kes(amount),
        'PartyA': msisdn,
        'PartyB': conf['shortcode'],
        'PhoneNumber': msisdn,
        'CallBackURL': conf['callback'],
        'AccountReference': 'SHOPEASE',
        'TransactionDesc': 'ShopEase Order',
    })
    if status == 200 and str(data.get('ResponseCode')) == '0':
        return {
            'checkout_request_id': data['CheckoutRequestID'],
            'merchant_request_id': data.get('MerchantRequestID', ''),
            'message': data.get('CustomerMessage', 'Check your phone to enter your M-Pesa PIN.'),
        }
    log.error('STK push rejected (%s): %s', status, data)
    raise MpesaError('M-Pesa did not accept the request. Check the number and try again.')


def stk_query(checkout_request_id):
    """
    Ask Daraja where a push stands. Returns {'result_code': int, 'result_desc': str} once the
    transaction has finished, or None while it is still being processed.
    """
    conf = _conf()
    password, ts = _password(conf)
    status, data = _post(conf, '/mpesa/stkpushquery/v1/query', {
        'BusinessShortCode': conf['shortcode'],
        'Password': password,
        'Timestamp': ts,
        'CheckoutRequestID': checkout_request_id,
    })
    if 'ResultCode' in data:
        try:
            return {'result_code': int(data['ResultCode']), 'result_desc': data.get('ResultDesc', '')}
        except (TypeError, ValueError):
            return None
    return None
