from django import forms


class RestockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(max_length=255, required=False)