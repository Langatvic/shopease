from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    city = forms.CharField(max_length=100)
    payment_method = forms.ChoiceField(
        choices=[('cod', 'Cash on Delivery')],
        initial='cod',
    )