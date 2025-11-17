from django import forms
from .models import Balance

class BalanceForm(forms.ModelForm):
    """Форма для створення та редагування записів про залишки зерна або відходів."""

    class Meta:
        model = Balance
        fields = [
            "place",
            "culture",
            "balance_type",
            "quantity",
        ]
        widgets = {
            "place": forms.Select(attrs={"class": "form-select"}),
            "culture": forms.Select(attrs={"class": "form-select"}),
            "balance_type": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "1",
                    "min": "0",
                    "placeholder": "Вкажіть кількість у тоннах",
                }
            ),
        }
        labels = {
            "date": "Дата запису",
            "place": "Місце зберігання",
            "culture": "Культура",
            "balance_type": "Тип балансу",
            "quantity": "Кількість (тонн)",
        }

    def clean_quantity(self):
        """Валідація кількості — не може бути від’ємною."""
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Кількість не може бути від’ємною.")
        return quantity

    def clean(self):
        """Додаткова перевірка на дублікати записів."""
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        place = cleaned_data.get("place")
        culture = cleaned_data.get("culture")
        balance_type = cleaned_data.get("balance_type")

        if all([date, place, culture, balance_type]):
            exists = Balance.objects.filter(
                date=date,
                place=place,
                culture=culture,
                balance_type=balance_type,
            ).exclude(pk=self.instance.pk).exists()
            if exists:
                raise forms.ValidationError(
                    "Запис із такими параметрами вже існує (ця дата, місце, культура та тип балансу)."
                )

        return cleaned_data