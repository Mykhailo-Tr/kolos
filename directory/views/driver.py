from ..models import Driver
from ..forms import DriverForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class DriverListView(BaseListView):
    model = Driver


class DriverCreateView(BaseCreateView):
    model = Driver
    form_class = DriverForm


class DriverUpdateView(BaseUpdateView):
    model = Driver
    form_class = DriverForm


class DriverDeleteView(BaseDeleteView):
    model = Driver
