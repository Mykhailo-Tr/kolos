from django.db import models
from django.conf import settings


class Driver(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ПІБ")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    
    class Meta:
        verbose_name = "Водій"
        verbose_name_plural = "Водії"
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Car(models.Model):
    number = models.CharField(max_length=20, verbose_name="Номер авто", unique=True)
    name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Назва / Коментар")
    default_driver = models.ForeignKey(
        "Driver",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cars",
        verbose_name="Закріплений водій"
    )
    
    class Meta:
        verbose_name = "Авто"
        verbose_name_plural = "Автомобілі"
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number}"


class Trailer(models.Model):
    number = models.CharField(max_length=20, verbose_name="Номер причепа")
    comment = models.CharField(max_length=100, blank=True, null=True, verbose_name="Коментар")
    
    class Meta:
        verbose_name = "Причеп"
        verbose_name_plural = "Причепи"
        ordering = ['number']
    
    def __str__(self):
        return self.number


class Culture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва культури / підкультури", unique=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcultures',
        verbose_name="Батьківська культура"
    )

    class Meta:
        unique_together = ('name', 'parent')
        verbose_name = "Культура / Підкультура"
        verbose_name_plural = "Культури / Підкультури"
        ordering = ['parent__name', 'name']

    def __str__(self):
        return f"{self.parent.name} — {self.name}" if self.parent else self.name
    
    @property
    def is_root(self):
        return self.parent is None

    
class Place(models.Model):
    name = models.CharField(max_length=150, verbose_name="Назва місця")
    place_type = models.CharField(
        max_length=50,
        choices=[
            ("storage", "Склад"),
            ("canopy", "Піднавіс"),
            ("factory", "Завод"),
            ("dryer", "Сушка"),
            ("other", "Інше"),
        ],
        default="storage",
        verbose_name="Тип місця"
    )
    
    class Meta:
        verbose_name = "Місце"
        verbose_name_plural = "Місця"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_place_type_display()})"


class Field(models.Model):
    name = models.CharField(max_length=150, verbose_name="Назва поля")
    
    class Meta:
        verbose_name = "Поле"
        verbose_name_plural = "Поля"
        ordering = ['name']

    def __str__(self):
        return self.name

