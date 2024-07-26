from django import forms
from TheApp.models import StoreItems


class StoreItemForm(forms.ModelForm):
    class Meta:
        model = StoreItems
        # You can specify fields here, e.g., ['item_name', 'item_price', 'item_photo']
        fields = '__all__'
