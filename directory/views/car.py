from ..models import Car
from ..forms import CarForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CarListView(BaseListView):
    model = Car
    sortable_fields = ["number", "name", "default_driver"]
    

class CarCreateView(BaseCreateView):
    model = Car
    form_class = CarForm


class CarUpdateView(BaseUpdateView):
    model = Car
    form_class = CarForm


class CarDeleteView(BaseDeleteView):
    model = Car
