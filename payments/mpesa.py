"""
Stub for M-Pesa Daraja API integration (future enhancement).
"""
import os


def stk_push(phone, amount, reference):
    """Send STK Push request to Safaricom Daraja API."""
    consumer_key = os.getenv('MPESA_CONSUMER_KEY')
    consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
    # TODO: authenticate → get token → call /mpesa/stkpush/v1/processrequest
    return {'success': False, 'message': 'M-Pesa integration not yet configured.'}