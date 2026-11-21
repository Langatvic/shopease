# ShopEase – E-commerce Platform

A web-based e-commerce management system built with Django 5, Bootstrap 5, and MySQL.

## Setup

```powershell
py -3.12 -m venv shop
.\shop\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver