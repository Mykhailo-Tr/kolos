from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
    last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
    phone = forms.CharField(max_length=20, required=False, label="Телефон")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone", "role", "password1", "password2"]


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username/Логін", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"}))
