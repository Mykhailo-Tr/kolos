import django_filters
from logistics.models import Trip

class TripFilter(django_filters.FilterSet):
    date_time = django_filters.DateFromToRangeFilter()
    culture = django_filters.CharFilter(field_name="culture__name", lookup_expr="icontains")
    sender = django_filters.CharFilter(field_name="sender__name", lookup_expr="icontains")
    car = django_filters.CharFilter(field_name="car__number", lookup_expr="icontains")

    class Meta:
        model = Trip
        fields = ["date_time", "culture", "sender", "car"]
