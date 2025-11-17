from django.urls import path
from . import views

urlpatterns = [
    path('', views.BalanceListView.as_view(), name='balance_list'),
    path('create/', views.BalanceCreateView.as_view(), name='balance_create'),
    path('<int:pk>/edit/', views.BalanceUpdateView.as_view(), name='balance_update'),
    path('<int:pk>/delete/', views.BalanceDeleteView.as_view(), name='balance_delete'),
]