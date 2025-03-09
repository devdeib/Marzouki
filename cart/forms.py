from django import forms
from TheApp.models import Size, Variation, Choices


class CartAddProductForm(forms.Form):
    override = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput)
    personalization = forms.CharField(max_length=100, required=False)
    variation = forms.CharField(
        max_length=100, required=False)  # Variation name
    choice = forms.CharField(max_length=100, required=False)     # Choice name

    def __init__(self, *args, **kwargs):
        item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)

        if item is not None and item.item_quantity > 0:
            quantity_choices = [(i, str(i))
                                for i in range(1, item.item_quantity + 1)]
        else:
            quantity_choices = [(0, '0')]

        self.fields['quantity'] = forms.TypedChoiceField(
            choices=quantity_choices, coerce=int, required=True)
