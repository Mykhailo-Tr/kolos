from django import forms
from dal import autocomplete
from django.utils.timezone import now
from .models import WeigherJournal, ShipmentJournal, FieldsIncome
from balances.models import Balance

         
class ForeignKeyQuerysetMixin:
    """Автоматично виставляє queryset-и для ForeignKey полів."""

    def set_foreignkey_querysets(self):
        from directory.models import Car, Trailer, Driver, Culture
        from logistics.models import Place

        mapping = {
            "driver": Driver,
            "car": Car,
            "trailer": Trailer,
            "culture": Culture,
            "from_place": Place,
            "to_place": Place,
            "place_from": Place,
            "place_to": Place,
        }

        for field_name, model in mapping.items():
            if field_name in self.fields:
                self.fields[field_name].queryset = model.objects.all()
                
         
class BaseJournalForm(ForeignKeyQuerysetMixin, forms.ModelForm):
    """
    Базова форма для журналів зважування.
    Містить спільні поля, валідацію та логіку розрахунку ваги нетто.
    """

    class Meta:
        # model визначатиметься у дочірніх класах
        fields = [
            "document_number",
            "date_time",
            "driver",
            "car",
            "trailer",
            "culture",
            "weight_gross",
            "weight_tare",
            "weight_loss",
            "note",
        ]
        widgets = {
            "document_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "№ документа або накладної",
            }),
            "date_time": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control",
                "value": now().strftime("%Y-%m-%dT%H:%M"),
            }),
            "driver": forms.Select(attrs={"class": "form-select"}),
            "car": forms.Select(attrs={"class": "form-select"}),
            "trailer": forms.Select(attrs={"class": "form-select"}),
            "culture": forms.Select(attrs={"class": "form-select"}),

            "weight_gross": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага брутто (тонн)"
            }),
            "weight_tare": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага тара (тонн)"
            }),
            "weight_loss": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага втрат (тонн)"
            }),

            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Примітка (необов’язково)",
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_foreignkey_querysets()

    def clean(self):
        """Перевіряє правильність вагових значень."""
        cleaned_data = super().clean()
        gross = cleaned_data.get("weight_gross")
        tare = cleaned_data.get("weight_tare")

        if gross is not None and tare is not None:
            if gross < tare:
                raise forms.ValidationError("Вага брутто не може бути меншою за тару.")

        return cleaned_data

    def save(self, commit=True):
        """Автоматичний розрахунок ваги нетто."""
        instance = super().save(commit=False)
        instance.weight_net = (instance.weight_gross or 0) - (instance.weight_tare or 0)
        if commit:
            instance.save()
        return instance

         
class WeigherJournalForm(BaseJournalForm):
    """ Форма для внутрішніх переміщень (WeigherJournal). """

    class Meta(BaseJournalForm.Meta):
        model = WeigherJournal
        base_fields = BaseJournalForm.Meta.fields.copy()
        base_fields[-1:-1] = ["from_place", "to_place"]
        fields = base_fields
        widgets = {
            **BaseJournalForm.Meta.widgets,
            "from_place": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце відправлення"
            }),
            "to_place": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце призначення"
            }),
        }

    def clean(self):
        """Додає логіку перевірки місць."""
        cleaned_data = super().clean()
        from_place = cleaned_data.get("from_place")
        to_place = cleaned_data.get("to_place")

        if not from_place or not to_place:
            raise forms.ValidationError("Необхідно вказати місця 'з' і 'до'.")

        if from_place == to_place:
            raise forms.ValidationError("Місця 'з' і 'до' не можуть бути однаковими.")

        return cleaned_data
    
    
    def clean_balance(self):
        """Перевірка наявності достатнього залишку в місці відправлення."""
        cleaned_data = super().clean()
        from_place = cleaned_data.get("from_place")
        culture = cleaned_data.get("culture")
        weight_net = cleaned_data.get("weight_net")

        if from_place and culture and weight_net is not None:
            try:
                balance = Balance.objects.get(
                    place=from_place,
                    culture=culture,
                    balance_type='stock'
                )
                if balance.quantity < weight_net:
                    raise forms.ValidationError(
                        f"Недостатньо залишку в місці {from_place.name} для культури {culture.name}."
                    )
            except Balance.DoesNotExist:
                raise forms.ValidationError(
                    f"Відсутній залишок в місці {from_place.name} для культури {culture.name}."
                )

        return cleaned_data


class ShipmentJournalForm(BaseJournalForm):
    """
    Форма для зовнішніх операцій (відвантаження зерна).
    Наслідує логіку з BaseJournalForm і додає місця відправлення/призначення.
    """

    class Meta(BaseJournalForm.Meta):
        model = ShipmentJournal
        base_fields = BaseJournalForm.Meta.fields.copy()
        base_fields[-1:-1] = ["action_type", "place_from", 
                              "place_to", "place_from_text", "place_to_text",]
        fields = base_fields
        widgets = {
            **BaseJournalForm.Meta.widgets,
            "action_type": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть тип операції"
            }),
            "place_from": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце відвантаження (з)"
            }),
            "place_from_text": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Вкажіть вручну, якщо не вибрано зі списку",
            }),
            "place_to": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце призначення (до)"
            }),
            "place_to_text": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Вкажіть вручну, якщо не вибрано зі списку",
            }),    
        }

    
class FieldsIncomeForm(BaseJournalForm):
    """ Форма для надходжень з полів (FieldsIncome). """

    class Meta(BaseJournalForm.Meta):
        model = FieldsIncome
        base_fields = BaseJournalForm.Meta.fields.copy()
        base_fields[-1:-1] = ["field", "place_to"]
        fields = base_fields
        widgets = {
            **BaseJournalForm.Meta.widgets,
            "field": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть поле відправлення"
            }),
            "place_to": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце прийому"
            }),
        }

    def clean(self):
        """Додає логіку перевірки місць."""
        cleaned_data = super().clean()
        field = cleaned_data.get("field")
        place_to = cleaned_data.get("place_to")

        if not field or not place_to:
            raise forms.ValidationError("Необхідно вказати поле відправлення і місце прийому.")

        if field == place_to:
            raise forms.ValidationError("Поле відправлення і місце прийому не можуть бути однаковими.")

        return cleaned_data
    
