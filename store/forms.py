from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('category', 'name', 'description', 'price', 'stock', 'image', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'image')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }