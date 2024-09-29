from django import forms
from TheApp.models import *
from django.forms.models import inlineformset_factory
from django.forms import inlineformset_factory


class StoreItemImageForm(forms.ModelForm):
    class Meta:
        model = StoreItemImage
        fields = ['image']  # Specify the field you want to appear in the form


class ItemVariationsForm(forms.ModelForm):
    class Meta:
        model = ItemVariation
        fields = ['variation']


VariationFormSet = inlineformset_factory(
    StoreItems, ItemVariation, form=ItemVariationsForm, extra=1, can_delete=True
)


class ChoicesForm(forms.ModelForm):
    # Adding the visibility field
    visible = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = Choices
        fields = ['name', 'price_increment', 'visible']  # Include 'visible'


ChoicesFormSet = inlineformset_factory(
    ItemVariation, Choices, form=ChoicesForm, extra=1, can_delete=True
)


class StoreItemForm(forms.ModelForm):
    class Meta:
        model = StoreItems
        fields = ['status', 'item_name', 'item_price', 'item_photo', 'item_description', 'item_quantity',
                  'tags', 'primary_color', 'secondary_color', 'video', 'width', 'height']
        widgets = {
            'status': forms.Select(choices=StoreItems.STATUS_CHOICES, attrs={'class': 'form-control'}),
            'item_photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'item_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'video': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class SectionForm(forms.ModelForm):
    items = forms.ModelMultipleChoiceField(
        queryset=StoreItems.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Section
        fields = ['name', 'items']


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['section', 'item', 'discount_type',
                  'discount_value', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class VariationForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ['name']


class ItemVariationForm(forms.ModelForm):
    class Meta:
        model = ItemVariation
        fields = ['item', 'variation']


# Create an inline formset for Choices related to an ItemVariation
ChoiceFormSet = inlineformset_factory(ItemVariation, Choices, fields=(
    'name', 'price_increment'), extra=1, can_delete=True)
