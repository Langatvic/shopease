from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('<str:order_number>/method/', views.payment_method, name='method'),
    path('<str:order_number>/cod/', views.cod_confirm, name='cod_confirm'),
    path('<str:order_number>/mpesa/', views.mpesa_stkpush, name='mpesa_stkpush'),
]