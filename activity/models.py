from django.db import models
from django.conf import settings
from django.utils import timezone


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Створення"),
        ("update", "Оновлення"),
        ("delete", "Видалення"),
        ("login", "Вхід у систему"),
        ("logout", "Вихід із системи"),
        ("view", "Перегляд"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="Користувач"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(verbose_name="Опис дії")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.get_action_display()} ({self.created_at:%d.%m.%Y %H:%M})"
    

