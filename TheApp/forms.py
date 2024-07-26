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


class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=200, required=False)