from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('directory/', include('directory.urls')),
    path('logistics/', include('logistics.urls')),
    path('waste/', include('waste.urls')),
    path('balances/', include('balances.urls')),
    # path("reports/", include("reports.urls")),
    path("activity/", include("activity.urls")),
]
