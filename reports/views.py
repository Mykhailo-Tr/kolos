from django.views.generic import TemplateView
from logistics.models import Trip
from django.db.models import Sum, F
from .filters import TripFilter

class ReportsIndexView(TemplateView):
    template_name = "reports/index.html"


from django_filters.views import FilterView
from .filters import TripFilter

class CultureReportView(FilterView):
    template_name = "reports/culture_report.html"
    filterset_class = TripFilter
    queryset = Trip.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = (
            self.object_list.values("culture__name")
            .annotate(total_net=Sum("weight_net"))
            .order_by("culture__name")
        )
        return ctx


class WarehouseReportView(TemplateView):
    template_name = "reports/warehouse_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = (
            Trip.objects.values("unloading_place__name")
            .annotate(total_net=Sum("weight_net"))
            .order_by("unloading_place__name")
        )
        return ctx


class DriverReportView(TemplateView):
    template_name = "reports/driver_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["report"] = (
            Trip.objects.values("driver__full_name", "car__number")
            .annotate(total_net=Sum("weight_net"))
            .order_by("driver__full_name")
        )
        return ctx


class BalanceReportView(TemplateView):
    template_name = "reports/balance_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # завезено (відправник → елеватор/склад)
        total_in = Trip.objects.aggregate(total=Sum("weight_net"))["total"] or 0
        # TODO: якщо треба "вивезено" окремо (наприклад, коли receiver != склад)
        # поки що простий баланс = завезено
        ctx["balance"] = {
            "in": total_in,
            "out": 0,
            "remain": total_in
        }
        return ctx
