from django import forms
from dal import autocomplete
from django.utils.timezone import now
from django.core.exceptions import ValidationError
# Припустимо, що моделі імпортовані з відповідних місць
from .models import WeigherJournal, ShipmentJournal, FieldsIncome, OtherIncome
from balances.models import Balance


# Додано вибір одиниць (повні назви)
UNIT_CHOICES = (
    ('t', 'Тонни (т)'),
    ('kg', 'Кілограми (кг)'),
)

         
class ForeignKeyQuerysetMixin:
    """Автоматично виставляє queryset-и для ForeignKey полів."""

    def set_foreignkey_querysets(self):
        # Припустимо, що ці моделі імпортовані з 'directory' та 'logistics'
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
    # Створюємо ТРИ ОКРЕМІ поля для одиниць виміру
    gross_unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="",
        initial='t',
        # Додаємо унікальний клас для кожної одиниці для JS
        widget=forms.Select(attrs={'class': 'form-select unit-switcher unit-switcher-gross'}) 
    )
    tare_unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="",
        initial='t',
        widget=forms.Select(attrs={'class': 'form-select unit-switcher unit-switcher-tare'}) 
    )
    loss_unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        label="",
        initial='t',
        widget=forms.Select(attrs={'class': 'form-select unit-switcher unit-switcher-loss'}) 
    )

    SMART_FIELDS = {
        "driver", "car", "trailer", "culture",
        "from_place", "to_place",
        "place_from", "place_to",
        "field"
    }

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

            # Вагові поля
            "weight_gross": forms.NumberInput(attrs={
                "class": "form-control weight-input", # Загальний клас для JS
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага брутто"
            }),
            "weight_tare": forms.NumberInput(attrs={
                "class": "form-control weight-input", # Загальний клас для JS
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага тара"
            }),
            "weight_loss": forms.NumberInput(attrs={
                "class": "form-control weight-input", # Загальний клас для JS
                "step": "0.001",
                "min": "0",
                "placeholder": "Вага втрат"
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

        for name, field in self.fields.items():
            if name in self.SMART_FIELDS:
                qs = getattr(field, "queryset", None)
                if qs is not None:
                    model = qs.model
                    field.smart_model = model._meta.model_name 
                else:
                    field.smart_model = ""

    def clean_weight_field(self, field_name):
        """
        Перевіряє та конвертує вагу згідно з обраною одиницею (всі значення в тоннах).
        Використовує динамічно визначене поле одиниці.
        """
        q = self.cleaned_data.get(field_name)
        
        # Визначаємо ім'я поля одиниці на основі імені вагового поля: weight_gross -> gross_unit
        unit_field_name = field_name.replace('weight_', '') + '_unit'

        # Отримуємо обрану одиницю з сирих даних
        unit = self.data.get(unit_field_name, 't') 

        if q is not None:
            if q < 0:
                raise forms.ValidationError("Вага не може бути від'ємною.") 
            
            # Логіка перетворення: Всі значення зберігаємо у ТОННАХ (t)
            if unit == 'kg':
                q = q / 1000 # Перетворюємо кілограми в тонни

        return q


    def clean(self):
        """Перевіряє правильність вагових значень та конвертує одиниці."""
        cleaned_data = super().clean()
        
        # Конвертуємо поля та оновлюємо cleaned_data конвертованими значеннями (в тоннах)
        gross = self.clean_weight_field("weight_gross")
        tare = self.clean_weight_field("weight_tare")
        loss = self.clean_weight_field("weight_loss")
        
        cleaned_data["weight_gross"] = gross
        cleaned_data["weight_tare"] = tare
        cleaned_data["weight_loss"] = loss

        if gross is not None and tare is not None:
            # Валідація: gross >= tare
            if gross < tare:
                self.add_error('weight_gross', ValidationError("Вага брутто не може бути меншою за тару."))

        if gross is not None and tare is not None and loss is not None:
             # Валідація: (gross - tare) >= loss
            if (gross - tare) < loss:
                 self.add_error('weight_loss', ValidationError("Вага втрат не може перевищувати вагу брутто мінус тара."))

        return cleaned_data

    def save(self, commit=True):
        """Автоматичний розрахунок ваги нетто."""
        instance = super().save(commit=False)
        # weight_net = gross - tare - loss
        instance.weight_net = (instance.weight_gross or 0) - (instance.weight_tare or 0) - (instance.weight_loss or 0)
        if commit:
            instance.save()
        return instance

         
class WeigherJournalForm(BaseJournalForm):
    """ Форма для внутрішніх переміщень (WeigherJournal). """

    class Meta(BaseJournalForm.Meta):
        model = WeigherJournal

        base_fields = BaseJournalForm.Meta.fields.copy()

        # Додаємо перемикач "зерно/відходи" одразу після культури
        culture_index = base_fields.index("culture")
        base_fields.insert(culture_index + 1, "to_balance_type")

        # from_place / to_place — як і раніше, перед note
        base_fields[-1:-1] = ["from_place", "to_place"]

        fields = base_fields

        widgets = {
            **BaseJournalForm.Meta.widgets,
            "to_balance_type": forms.RadioSelect(
                attrs={'class': 'balance-type-toggle-input'}
            ),
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
        """Додає логіку перевірки місць та балансу."""
        cleaned_data = super().clean()
        from_place = cleaned_data.get("from_place")
        to_place = cleaned_data.get("to_place")
        culture = cleaned_data.get("culture")

        if not from_place or not to_place:
            if not from_place:
                self.add_error('from_place', ValidationError("Необхідно вказати місце відправлення."))
            if not to_place:
                self.add_error('to_place', ValidationError("Необхідно вказати місце призначення."))

        if from_place and to_place and from_place == to_place:
            raise forms.ValidationError("Місця 'з' і 'до' не можуть бути однаковими.")

        # Повна вага, що ФІЗИЧНО виїжджає з from_place (gross - tare).
        # Саме цю суму списує WeigherJournal.update_balance(), а не "нетто".
        gross = cleaned_data.get("weight_gross") or 0
        tare = cleaned_data.get("weight_tare") or 0
        departed = gross - tare

        if from_place and culture and departed > 0:
            # Якщо це РЕДАГУВАННЯ і from_place/culture НЕ змінились — під час
            # save() спочатку відкотиться СТАРЕ списання (departed_weight
            # старого запису), тож цю суму потрібно врахувати як вже "доступну",
            # навіть якщо поточний баланс її ще не відображає.
            already_reserved = 0
            if (
                self.instance.pk
                and self.instance.from_place_id == from_place.id
                and self.instance.culture_id == culture.id
            ):
                already_reserved = self.instance.departed_weight

            available = None
            try:
                balance = Balance.objects.get(
                    place=from_place,
                    culture=culture,
                    balance_type='stock'
                )
                available = balance.quantity + already_reserved
            except Balance.DoesNotExist:
                if already_reserved > 0:
                    available = already_reserved
                else:
                    self.add_error('from_place',
                                   ValidationError(
                                       f"Відсутній залишок (Balance) в місці {from_place.name} для культури {culture.name}."
                                   ))

            if available is not None and available < departed:
                self.add_error('weight_gross',
                    ValidationError(
                    f"Недостатньо залишку в місці {from_place.name} для культури {culture.name}. "
                    f"Потрібно списати {departed:.3f} т (брутто - тара), "
                    f"доступно: {available:.3f} т."
                ))

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
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Додайте валідацію, специфічну для ShipmentJournal, тут, якщо вона потрібна
        
        return cleaned_data

    
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
        """Додає логіку перевірки полів."""
        cleaned_data = super().clean()
        field = cleaned_data.get("field")
        place_to = cleaned_data.get("place_to")

        if not field:
            self.add_error('field', ValidationError("Необхідно вказати поле відправлення."))
        
        if not place_to:
            self.add_error('place_to', ValidationError("Необхідно вказати місце прийому."))

        return cleaned_data
    
class OtherIncomeForm(BaseJournalForm):
    """ Форма для інших надходжень (OtherIncome). """

    class Meta(BaseJournalForm.Meta):
        model = OtherIncome
        base_fields = BaseJournalForm.Meta.fields.copy()
        base_fields[-1:-1] = ["seller", "place_to"]
        fields = base_fields
        widgets = {
            **BaseJournalForm.Meta.widgets,
            "seller": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Продавець або джерело надходження",
            }),
            "place_to": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Оберіть місце прийому"
            }),
        }

    def clean(self):
        """Додає логіку перевірки продавця та місця прийому."""
        cleaned_data = super().clean()
        seller = cleaned_data.get("seller")
        place_to = cleaned_data.get("place_to")

        if not seller:
            self.add_error('seller', ValidationError("Необхідно вказати продавця або джерело надходження."))
        
        if not place_to:
            self.add_error('place_to', ValidationError("Необхідно вказати місце прийому."))

        return cleaned_data