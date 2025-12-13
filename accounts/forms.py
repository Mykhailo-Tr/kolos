from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.validators import RegexValidator
from .models import User


# Валідатор для номера телефону
phone_validator = RegexValidator(
    regex=r'^\+?\d{9,15}$', 
    message="Номер телефону має бути в міжнародному форматі (наприклад, +380XXXXXXXXX). Дозволено 9-15 цифр."
)


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50, 
        required=True, 
        label="Ім'я",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        max_length=50, 
        required=True, 
        label="Прізвище",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    phone = forms.CharField(
        max_length=20, 
        required=False, 
        label="Телефон",
        validators=[phone_validator], # <-- ДОДАНО ВАЛІДАЦІЮ
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+380XXXXXXXXX"})
    )
    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label="Підтвердження пароля",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone", "role", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Встановлюємо клас для інших полів через цикл, щоб не дублювати
        for field_name in ['username', 'role']:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username/Логін", widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"}))


class EditProfileForm(forms.ModelForm):
    # Явно перевизначаємо phone, щоб додати валідатор
    phone = forms.CharField(
        max_length=20, 
        required=False, 
        label="Телефон",
        validators=[phone_validator], # <-- ДОДАНО ВАЛІДАЦІЮ
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+380XXXXXXXXX"})
    )
    
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone"]  # role не даємо редагувати
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            # "phone" вже перевизначено вище з валідатором
        }
        labels = {"username": "Логін", "first_name": "Ім'я", "last_name": "Прізвище", "phone": "Телефон",}


# Нова форма для зміни пароля (для використання в edit_profile_view)
class ChangePasswordForm(PasswordChangeForm):
    # Перевизначаємо віджети для застосування класу form-control
    old_password = forms.CharField(
        label="Поточний пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password1 = forms.CharField(
        label="Новий пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password2 = forms.CharField(
        label="Підтвердження нового пароля",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Прибираємо email, якщо він є у базовому класі
        if 'email' in self.fields:
            del self.fields['email']