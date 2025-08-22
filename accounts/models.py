from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Адміністратор"
        WEIGHER = "weigher", "Вагар"
        
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.WEIGHER
    )

    phone = models.CharField(max_length=20, blank=True, null=True)
    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
