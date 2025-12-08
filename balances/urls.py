from django.urls import path
from . import views



urlpatterns = [
    path('', views.BalanceListView.as_view(), name='balance_list'),
    path('create/', views.BalanceCreateView.as_view(), name='balance_create'),
    path('<int:pk>/edit/', views.BalanceUpdateView.as_view(), name='balance_update'),
    path('<int:pk>/delete/', views.BalanceDeleteView.as_view(), name='balance_delete'),
    
    path('history/empty/create/', views.EmptySnapshotCreateView.as_view(), name='balance_snapshot_empty_create'),
    path('history/empty/quick-create/', views.QuickEmptySnapshotCreateView.as_view(), name='balance_snapshot_quick_create'),

    path('history/', views.BalanceSnapshotListView.as_view(), name='balance_snapshot_list'),
    path('history/create/', views.BalanceSnapshotCreateView.as_view(), name='balance_snapshot_create'),
    path('history/<int:pk>/', views.BalanceSnapshotDetailView.as_view(), name='balance_snapshot_detail'),
    path('history/<int:pk>/edit/', views.BalanceSnapshotUpdateView.as_view(), name='balance_snapshot_update'),
    path('history/<int:pk>/delete/', views.BalanceSnapshotDeleteView.as_view(), name='balance_snapshot_delete'),
    path('history/<int:snapshot_pk>/add-record/', views.BalanceHistoryCreateView.as_view(), name='balance_history_create'),
]