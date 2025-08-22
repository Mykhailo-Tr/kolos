from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Ролі користувачів
    class Roles(models.TextChoices):
        ADMIN = "admin", "Адміністратор"
        WEIGHER = "weigher", "Вагар"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.DRIVER
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
