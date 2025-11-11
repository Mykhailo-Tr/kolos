from ..models import Culture
from ..forms import CultureForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class CultureListView(BaseListView):
    model = Culture


class CultureCreateView(BaseCreateView):
    model = Culture
    form_class = CultureForm


class CultureUpdateView(BaseUpdateView):
    model = Culture
    form_class = CultureForm


class CultureDeleteView(BaseDeleteView):
    model = Culture
