from ..models import Field
from ..forms import FieldForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class FieldListView(BaseListView):
    model = Field
    sortable_fields = ["name"]


class FieldCreateView(BaseCreateView):
    model = Field
    form_class = FieldForm


class FieldUpdateView(BaseUpdateView):
    model = Field
    form_class = FieldForm


class FieldDeleteView(BaseDeleteView):
    model = Field
