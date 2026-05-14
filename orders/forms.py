from django import forms
from .models import Order

COUNTRY_CHOICES = [
    ('', 'Country / Region'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('SY', 'Syria'),
    ('SA', 'Saudi Arabia'),
    ('AE', 'United Arab Emirates'),
    ('TR', 'Turkey'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('CA', 'Canada'),
    ('AU', 'Australia'),
    # Add more as needed
]


class OrderCreateForm(forms.ModelForm):
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=True,
        error_messages={'required': 'Please select a country.',
                        'invalid_choice': 'Please select a valid country.'}
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        error_messages={'required': 'Phone number is required.'}
    )

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone',
                  'address', 'postal_code', 'city', 'country']
