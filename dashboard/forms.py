from django import forms
from TheApp.models import *
from django.forms.models import inlineformset_factory
from django.forms import inlineformset_factory


class ItemVariationsForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ItemVariation
        fields = ['id', 'variation']
        widgets = {
            'variation': forms.Select(attrs={'class': 'form-control'})
        }


class ChoiceForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Choices
        fields = ['id', 'name', 'price_increment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price_increment': forms.NumberInput(attrs={'class': 'form-control'})
        }


# Update formset definitions
ItemVariationsFormSet = inlineformset_factory(
    StoreItems,
    ItemVariation,
    form=ItemVariationsForm,
    fields=['id', 'variation'],
    extra=1,
    can_delete=True
)

ChoiceFormSet = inlineformset_factory(
    ItemVariation,
    Choices,
    form=ChoiceForm,
    fields=['id', 'name', 'price_increment'],
    extra=1,
    can_delete=True
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
            'item_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'item_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'primary_color': forms.Select(attrs={'class': 'form-control'}),
            'secondary_color': forms.Select(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StoreItemImageForm(forms.ModelForm):
    class Meta:
        model = StoreItemImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }


class StoreItemVideoForm(forms.ModelForm):
    class Meta:
        model = StoreItemVideo
        fields = ['video_file']
        widgets = {
            'video_file': forms.FileInput(attrs={'class': 'form-control'})
        }


# Create formsets for multiple images and videos
StoreItemImageFormSet = inlineformset_factory(
    StoreItems,
    StoreItemImage,
    form=StoreItemImageForm,
    extra=1,
    can_delete=True
)

StoreItemVideoFormSet = inlineformset_factory(
    StoreItems,
    StoreItemVideo,
    form=StoreItemVideoForm,
    extra=1,
    can_delete=True
)



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


class VariationCreateForm(forms.ModelForm):
    class Meta:
        model = Variation
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class ItemVariationForm(forms.ModelForm):
    class Meta:
        model = ItemVariation
        fields = ['item', 'variation']


# Create an inline formset for Choices related to an ItemVariation
ChoiceFormSet = inlineformset_factory(ItemVariation, Choices, fields=(
    'name', 'price_increment'), extra=1, can_delete=True)
