from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20, help_text='Used for delivery and, if you pay with M-Pesa, for the payment prompt.')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    city = forms.CharField(max_length=100)
    payment_method = forms.ChoiceField(
        label='Payment method',
        choices=[('mpesa', 'M-Pesa (pay now with a prompt on your phone)'),
                 ('cod', 'Cash on delivery (pay when your order arrives)')],
        widget=forms.RadioSelect,
        initial='mpesa',
    )
