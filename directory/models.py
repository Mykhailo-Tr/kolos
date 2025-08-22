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
    trailer = models.CharField(max_length=20, blank=True, null=True, verbose_name="Причеп")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Водій")

    def __str__(self):
        return f"{self.number}" + (f" / {self.trailer}" if self.trailer else "")


class Culture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Культура", unique=True)

    def __str__(self):
        return self.name
