from django import forms
from .models import Culture, Driver, Car, Trailer

class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Назва культури"})
        }


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ["full_name", "phone", "company"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "ПІБ водія"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Телефон"}),
            "company": forms.TextInput(attrs={"class": "form-control", "placeholder": "Компанія"}),
        }
        required_fields = ["full_name"]
        
    def clean_full_name(self):
        full_name = self.cleaned_data.get("full_name")
        if not full_name:
            raise forms.ValidationError("ПІБ водія є обов'язковим.")
        return full_name
    
    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        import re
        # Accepts international numbers with +, spaces, dashes, parentheses, and digits
        pattern = r"^\+?[\d\s\-\(\)]{7,20}$"
        if phone and not re.match(pattern, phone):
            raise forms.ValidationError("Введіть коректний номер телефону.")
        return phone
    
    
class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ["number", "comment"]
        widgets = {
            "number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Номер авто"}),
            "comment": forms.TextInput(attrs={"class": "form-control", "placeholder": "Коментар"}),
        }
        
    def clean_number(self):
        number = self.cleaned_data.get("number")
        if not number:
            raise forms.ValidationError("Номер авто є обов'язковим.")
        return number
    

class TrailerForm(forms.ModelForm):
    class Meta:
        model = Trailer
        fields = ["number", "comment"]
        widgets = {
            "number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Номер причепа"}),
            "comment": forms.TextInput(attrs={"class": "form-control", "placeholder": "Коментар"}),
        }
        
    def clean_number(self):
        number = self.cleaned_data.get("number")
        if not number:
            raise forms.ValidationError("Номер причепа є обов'язковим.")
        return number