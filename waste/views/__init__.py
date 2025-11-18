from .views import WasteJournalListView
from .views_utilization import (
    UtilizationCreateView, UtilizationUpdateView, UtilizationDeleteView
)
from .views_recycling import (
    RecyclingCreateView, RecyclingUpdateView, RecyclingDeleteView
)

__all__ = [
    'WasteJournalListView',
    'UtilizationCreateView', 'UtilizationUpdateView', 'UtilizationDeleteView',
    'RecyclingCreateView', 'RecyclingUpdateView', 'RecyclingDeleteView',
]