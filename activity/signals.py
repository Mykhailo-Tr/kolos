from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import ActivityLog

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(user=user, action="login", description="Користувач увійшов у систему")

@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    if user.is_authenticated:
        ActivityLog.objects.create(user=user, action="logout", description="Користувач вийшов із системи")
