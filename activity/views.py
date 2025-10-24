from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import ActivityLog
from django.contrib.auth.decorators import login_required

@login_required
def activity_list(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    filter_period = request.GET.get("period", "today")
    logs = ActivityLog.objects.filter(user=request.user)

    if filter_period == "week":
        logs = logs.filter(created_at__gte=week_ago)
    elif filter_period == "month":
        logs = logs.filter(created_at__gte=month_ago)
    elif filter_period == "all":
        pass  # всі дії
    else:
        logs = logs.filter(created_at__date=today)

    return render(request, "activity/activity_list.html", {
        "logs": logs,
        "filter_period": filter_period,
    })
