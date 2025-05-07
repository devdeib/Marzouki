from .models import ArtistProfile
from django import forms
from TheApp.models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
import random
from django.contrib.auth import get_user_model


class SignupForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = UserProfile(user=user)
            profile.save()
        return user


class NewsletterSubscriptionForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        }

class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=200, required=False)


class ArtistBioForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = ['bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }


class ArtistPhotoForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = ['photo']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class SocialProfilesForm(forms.Form):
    twitter_url = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={'placeholder': 'https://twitter.com/username'})
    )
    twitter_active = forms.BooleanField(required=False, initial=True)
    instagram_url = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={'placeholder': 'https://instagram.com/username'})
    )
    instagram_active = forms.BooleanField(required=False, initial=True)
    facebook_url = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={'placeholder': 'https://facebook.com/username'})
    )
    facebook_active = forms.BooleanField(required=False, initial=True)
