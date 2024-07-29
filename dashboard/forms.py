from django import forms
from TheApp.models import StoreItems, StoreItemImage



class StoreItemImageForm(forms.ModelForm):
    class Meta:
        model = StoreItemImage
        fields = ['image']  # Specify the field you want to appear in the form


class StoreItemForm(forms.ModelForm):
    class Meta:
        model = StoreItems
        fields = '__all__'
