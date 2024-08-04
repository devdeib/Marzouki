from django import forms
from TheApp.models import StoreItems, StoreItemImage, Section



class StoreItemImageForm(forms.ModelForm):
    class Meta:
        model = StoreItemImage
        fields = ['image']  # Specify the field you want to appear in the form


class StoreItemForm(forms.ModelForm):
    class Meta:
        model = StoreItems
        fields = '__all__'
        
        
class SectionForm(forms.ModelForm):
    items = forms.ModelMultipleChoiceField(
        queryset=StoreItems.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Section
        fields = ['name', 'items']
