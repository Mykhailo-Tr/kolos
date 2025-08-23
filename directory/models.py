from django.db import models
from django.conf import settings


class Driver(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ПІБ")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name="Компанія")

    def __str__(self):
        return self.full_name


class Car(models.Model):
    number = models.CharField(max_length=20, verbose_name="Номер авто")
    comment = models.CharField(max_length=100, blank=True, null=True, verbose_name="Коментар")
    
    def __str__(self):
        return f"{self.number}"
    

class Trailer(models.Model):
    number = models.CharField(max_length=20, verbose_name="Номер причепа")
    comment = models.CharField(max_length=100, blank=True, null=True, verbose_name="Коментар")
    
    def __str__(self):
        return self.number


class Culture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Культура", unique=True)

    def __str__(self):
        return self.name
    

class UnloadingPlace(models.Model):
    name = models.CharField(max_length=150, verbose_name="Назва місця")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адреса")
    place_type = models.CharField(
        max_length=50,
        choices=[
            ("elevator", "Елеватор"),
            ("warehouse", "Склад"),
            ("factory", "Завод"),
            ("other", "Інше"),
        ],
        default="elevator",
        verbose_name="Тип місця"
    )

    def __str__(self):
        return f"{self.name} ({self.get_place_type_display()})"
    

class Partner(models.Model):
    """Відправники / Отримувачі"""
    name = models.CharField(max_length=150, verbose_name="Назва")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    partner_type = models.CharField(
        max_length=20,
        choices=[
            ("sender", "Відправник"),
            ("receiver", "Отримувач"),
            ("both", "Відправник та отримувач"),
        ],
        default="sender",
        verbose_name="Тип партнера"
    )

    def __str__(self):
        return f"{self.name} ({self.get_partner_type_display()})"

