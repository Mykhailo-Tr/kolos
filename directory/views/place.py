from ..models import Place
from ..forms import PlaceForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class PlaceListView(BaseListView):
    model = Place


class PlaceCreateView(BaseCreateView):
    model = Place
    form_class = PlaceForm


class PlaceUpdateView(BaseUpdateView):
    model = Place
    form_class = PlaceForm


class PlaceDeleteView(BaseDeleteView):
    model = Place
