from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from datetime import datetime

date_now = datetime.today()
pay_day = datetime(2026, 8, 29)

is_payday = False

if date_now < pay_day and not is_payday:
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('accounts.urls')),
        path('directory/', include('directory.urls')),
        path('logistics/', include('logistics.urls')),
        path('waste/', include('waste.urls')),
        path('balances/', include('balances.urls')),
        path("reports/", include("reports.urls")),
    ]
else:
    urlpatterns = [
        path('', TemplateView.as_view(template_name="payday.html"))
    ]
