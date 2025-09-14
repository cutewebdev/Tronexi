from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_over_18 = forms.BooleanField(required=True, label="I am 18 years or older")

    class Meta:
        model = CustomUser
        fields = [
            'full_name',
            'username',
            'email',
            'phone_number',
            'gender',
            'country',
            'currency',
            'referral_code',
            'password1',
            'password2',
            'is_over_18',
        ]
        widgets = {
            'gender': forms.Select(choices=CustomUser._meta.get_field('gender').choices),
            'country': forms.Select(choices=CustomUser._meta.get_field('country').choices),
            'currency': forms.Select(choices=CustomUser._meta.get_field('currency').choices),
        }
