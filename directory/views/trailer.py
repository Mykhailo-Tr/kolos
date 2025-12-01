from ..models import Trailer
from ..forms import TrailerForm
from .base import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView


class TrailerListView(BaseListView):
    model = Trailer
    sortable_fields = ["number", "comment"]



class TrailerCreateView(BaseCreateView):
    model = Trailer
    form_class = TrailerForm


class TrailerUpdateView(BaseUpdateView):
    model = Trailer
    form_class = TrailerForm


class TrailerDeleteView(BaseDeleteView):
    model = Trailer
