from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('update/<int:product_id>/', views.stock_update, name='stock_update'),
    path('log/', views.stock_log, name='stock_log'),
]