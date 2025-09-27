from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.conf import settings

from logistics.models import WeigherJournal, ShipmentJournal, ArrivalJournal, StockBalance
from .views import _day_range_for_date
from .services import unify_rows_from_querysets, aggregate_rows, compute_stock_balance

from .send_utils import (
    generate_daily_csv_string,
    generate_stock_balance_csv_string,
    send_report_to_server,
)

import datetime


@require_POST
def send_report(request):
    """
    AJAX endpoint: /reports/send/ 
    Очікує POST JSON/body або form-encoded:
    - report_type: daily | stock_balance
    - date: YYYY-MM-DD (для daily) optional -> default selected date or today
    - group_by: якщо daily
    - mode: for stock_balance -> 'period' or 'current'
    - date_from/date_to for stock_balance period mode (YYYY-MM-DD)
    """
    report_type = request.POST.get("report_type") or request.headers.get("X-REPORT-TYPE")
    print("send_report called with type:", report_type)
    if not report_type:
        return HttpResponseBadRequest("Missing report_type")

    # DAILY
    if report_type == "daily":
        # reuse your existing logic to build report
        date_str = request.POST.get("date")
        group_by = request.POST.get("group_by", "none")
        default_name = "daily_report_{date_str}_{group_by}_{date_str}.csv".format(date_str=date_str, group_by=group_by)
        name = request.POST.get("name", default_name)
        # parse date
        if date_str:
            try:
                date = datetime.date.fromisoformat(date_str)
            except Exception as er:
                print(f'Error parsing date "{date_str}":', er)
                return HttpResponseBadRequest("Invalid date")
        else:
            date = datetime.date.today()

        # ВАЖЛИВО: reuse functions from your module: _day_range_for_date, unify_rows_from_querysets, aggregate_rows
        # Тут припускаю вони імпортовані або доступні у цьому модулі.
        start_dt, end_dt = _day_range_for_date(date)
        # base querysets (use same select_related/filters as daily_report)
        w_qs = WeigherJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender", "receiver").filter(date_time__gte=start_dt, date_time__lte=end_dt)
        s_qs = ShipmentJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender").filter(date_time__gte=start_dt, date_time__lte=end_dt)
        a_qs = ArrivalJournal.objects.select_related("car", "driver", "trailer", "culture", "unloading_place", "sender_or_receiver").filter(date_time__gte=start_dt, date_time__lte=end_dt)

        # optional filters (you can pass car,driver,culture ids)
        for f in ("car", "driver", "culture", "sender", "unloading_place"):
            val = request.POST.get(f)
            if val:
                kwargs = {f: val}
                w_qs = w_qs.filter(**{f: val})
                s_qs = s_qs.filter(**{f: val})
                a_qs = a_qs.filter(**{f: val})

        rows = unify_rows_from_querysets(w_qs, s_qs, a_qs)
        report = aggregate_rows(rows, group_by=group_by)
        csv_content = generate_daily_csv_string(report, date)
        result = send_report_to_server(name, csv_content)
        
        return JsonResponse({"sent": result["ok"], "status": result["status_code"], "response": result["response"], "error": result["error"]})

    # STOCK BALANCE
    elif report_type == "stock_balance":
        mode = request.POST.get("mode", "period")
        default_name = "stock_balance_report_{mode}.csv".format(mode=mode)
        name = request.POST.get("name", default_name)
        print("default_name:", default_name)
        print("name:", name)
        print("mode:", mode)
        if mode == "period":
            date_from = request.POST.get("date_from")
            date_to = request.POST.get("date_to")
            try:
                df = datetime.date.fromisoformat(date_from) if date_from else None
                dt = datetime.date.fromisoformat(date_to) if date_to else None
            except Exception as er:
                print(er)
                return HttpResponseBadRequest("Invalid date_from/date_to", er)

            unloading_place = request.POST.get("unloading_place") or None
            culture = request.POST.get("culture") or None
            driver = request.POST.get("driver") or None
            car = request.POST.get("car") or None

            rows = compute_stock_balance(
                df, dt,
                unloading_place=unloading_place,
                culture=culture,
                driver=driver,
                car=car
            )
            fname, csv_content = generate_stock_balance_csv_string("period", rows, {"date_from": date_from, "date_to": date_to})
        else:
            qs = StockBalance.objects.all()
            rows = [{"place_name": sb.unloading_place.name, "culture": sb.culture.name, "balance": sb.quantity} for sb in qs]
            fname, csv_content = generate_stock_balance_csv_string("current", rows)

        result = send_report_to_server(name, csv_content)
        return JsonResponse({"sent": result["ok"], "status": result["status_code"], "response": result["response"], "error": result["error"]})

    else:
        return JsonResponse({"sent": False, "error": "Unknown report_type"}, status=400)
