from django import forms
from TheApp.models import Size, Variation


class CartAddProductForm(forms.Form):
    override = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput)
    personalization = forms.CharField(max_length=100, required=False)
    size = forms.ModelChoiceField(queryset=Size.objects.all(), required=False)
    variation = forms.ModelChoiceField(
        queryset=Variation.objects.all(), required=False)

    def __init__(self, *args, **kwargs):  # This line should have double underscores
        item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)  # This line also should have double underscores

        if item is not None and item.item_quantity > 0:
            quantity_choices = [(i, str(i))
                                for i in range(1, item.item_quantity + 1)]
        else:
            quantity_choices = [(0, '0')]

        self.fields['quantity'] = forms.TypedChoiceField(
            choices=quantity_choices, coerce=int, required=True)
