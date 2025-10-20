from .models import ActivityLog

def log_activity(user, action, description):
    """Записує активність користувача у БД."""
    if user.is_authenticated:
        ActivityLog.objects.create(user=user, action=action, description=description)