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
    widgets = {
        'variation': forms.Select(attrs={'class': 'form-control'})
    }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choices
        fields = ['name', 'price_increment']


ItemVariationsFormSet = inlineformset_factory(
    StoreItems,
    ItemVariation,
    form=ItemVariationsForm,
    extra=1,
    can_delete=True,
    validate_min=False
)

ChoiceFormSet = inlineformset_factory(
    ItemVariation,
    Choices,
    form=ChoiceForm,
    extra=1,
    can_delete=True,
    validate_min=False
)


class StoreItemForm(forms.ModelForm):
    class Meta:
        model = StoreItems
        fields = ['status', 'item_name', 'item_description', 'item_photo', 'item_price', 'item_quantity',
                  'tags', 'primary_color', 'secondary_color', 'width', 'height']
        widgets = {
            'status': forms.Select(choices=StoreItems.STATUS_CHOICES, attrs={'class': 'form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'item_photo': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
            'item_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'primary_color': forms.Select(attrs={'class': 'form-control'}),
            'secondary_color': forms.Select(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
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

    def __init__(self, *args, **kwargs):
        super(VariationForm, self).__init__(*args, **kwargs)
        # Apply Bootstrap Lux theme to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ItemVariationForm(forms.ModelForm):
    class Meta:
        model = ItemVariation
        fields = ['item', 'variation']


# Create an inline formset for Choices related to an ItemVariation
ChoiceFormSet = inlineformset_factory(ItemVariation, Choices, fields=(
    'name', 'price_increment'), extra=1, can_delete=True)
