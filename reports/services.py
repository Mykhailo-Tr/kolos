from django.db.models import Sum, F, Count
from logistics.models import WeigherJournal, ShipmentJournal, ArrivalJournal
from collections import defaultdict
from decimal import Decimal


def get_culture_stats(qs):
    return list(
        qs.values("culture_id", "culture__name")
        .annotate(total_net=Sum(F("weight_gross") - F("weight_tare")))
        .order_by("culture__name")
    )


def get_driver_stats(qs):
    return list(
    qs.values("driver_id", "driver__full_name")
        .annotate(total_net=Sum(F("weight_gross") - F("weight_tare")))
        .order_by("driver__full_name")
    )


def get_car_stats(qs):
    return list(
        qs.values("car_id", "car__number")
        .annotate(total_net=Sum(F("weight_gross") - F("weight_tare")))
        .order_by("car__number")
    )


def get_unloading_stats(qs):
    return list(
        qs.values("unloading_place_id", "unloading_place__name")
        .annotate(total_net=Sum(F("weight_gross") - F("weight_tare")))
        .order_by("unloading_place__name")
    )


def get_balance(qs, sender_field="sender", receiver_field="receiver", use_single_field=False):
    """
    Баланс по відправнику/отримувачу.
    Якщо use_single_field=True — використовується одне поле (sender_or_receiver).
    """

    if use_single_field:
        balance = qs.values(
            f"{receiver_field}_id", f"{receiver_field}__name"
        ).annotate(
            total_net=Sum(F("weight_gross") - F("weight_tare"))
        )
        return {"partners": list(balance)}

    # стандартний варіант (WeigherJournal / ShipmentJournal)
    by_sender = qs.values(f"{sender_field}_id", f"{sender_field}__name").annotate(
        total_net=Sum(F("weight_gross") - F("weight_tare"))
    )

    by_receiver = qs.values(f"{receiver_field}_id", f"{receiver_field}__name").annotate(
        total_net=Sum(F("weight_gross") - F("weight_tare"))
    )

    return {
        "senders": list(by_sender),
        "receivers": list(by_receiver),
    }
    
    
def _zero():
    return {"gross": Decimal("0"), "tare": Decimal("0"), "net": Decimal("0")}

def unify_rows_from_querysets(weigher_qs, shipment_qs, arrival_qs):
    """
    Приводимо всі записи до єдиного списку dict-рядків.
    Очікуємо, що передані QuerySets вже відфільтровані по даті/фільтрам.
    Кожен рядок: dict with keys:
      - type: 'weigher' | 'shipment' | 'arrival'
      - date_time
      - car, driver, trailer, culture, unloading_place, sender, receiver
      - gross, tare, net (Decimal)
      - obj (optional) original object for modal details
    """
    rows = []

    for obj in weigher_qs:
        rows.append({
            "type": "weigher",
            "date_time": obj.date_time,
            "car": obj.car,
            "driver": obj.driver,
            "trailer": obj.trailer,
            "culture": obj.culture,
            "unloading_place": obj.unloading_place,
            "sender": getattr(obj, "sender", None),
            "receiver": getattr(obj, "receiver", None),
            "gross": obj.weight_gross or 0,
            "tare": obj.weight_tare or 0,
            "net": obj.weight_net or 0,
            "obj": obj,
        })

    for obj in shipment_qs:
        rows.append({
            "type": "shipment",
            "date_time": obj.date_time,
            "car": obj.car,
            "driver": obj.driver,
            "trailer": obj.trailer,
            "culture": obj.culture,
            "unloading_place": obj.unloading_place,
            "sender": getattr(obj, "sender", None),
            "receiver": None,
            "gross": obj.weight_gross or 0,
            "tare": obj.weight_tare or 0,
            "net": obj.weight_net or 0,
            "obj": obj,
        })

    for obj in arrival_qs:
        rows.append({
            "type": "arrival",
            "date_time": obj.date_time,
            "car": obj.car,
            "driver": obj.driver,
            "trailer": obj.trailer,
            "culture": obj.culture,
            "unloading_place": obj.unloading_place,
            "sender": None,
            "receiver": getattr(obj, "sender_or_receiver", None),
            "gross": obj.weight_gross or 0,
            "tare": obj.weight_tare or 0,
            "net": obj.weight_net or 0,
            "obj": obj,
        })

    return rows

def aggregate_rows(rows, group_by="none"):
    """
    Агрегує rows по групі.
    Додає список trips у кожен рядок таблиці для детального відображення.
    """
    def get_group(row):
        if group_by == "none":
            return getattr(row["unloading_place"], "name", "Без місця") if row.get("unloading_place") else "Без місця"
        if group_by == "culture":
            return getattr(row["culture"], "name", "Без культури") if row.get("culture") else "Без культури"
        if group_by == "driver":
            return getattr(row["driver"], "full_name", "Без водія") if row.get("driver") else "Без водія"
        if group_by == "car":
            return getattr(row["car"], "number", "Без авто") if row.get("car") else "Без авто"
        if group_by == "trailer":
            return getattr(row["trailer"], "number", "Без причепа") if row.get("trailer") else "Без причепа"
        if group_by == "sender":
            return getattr(row.get("sender") or row.get("receiver"), "name", "Без партнера")
        if group_by == "unloading_place":
            return getattr(row["unloading_place"], "name", "Без місця") if row.get("unloading_place") else "Без місця"
        return "Інше"

    def _zero_with_trips():
        return {"gross": Decimal("0"), "tare": Decimal("0"), "net": Decimal("0"), "trips": []}

    totals_by_group_and_culture = defaultdict(lambda: defaultdict(_zero_with_trips))
    groups_summary = defaultdict(_zero)
    totals = {"gross_in": Decimal("0"), "net_in": Decimal("0"), "gross_out": Decimal("0"), "net_out": Decimal("0")}

    for row in rows:
        group = get_group(row)
        culture_name = getattr(row.get("culture"), "name", None) or "Без культури"
        gross = Decimal(row.get("gross") or 0)
        tare = Decimal(row.get("tare") or 0)
        net = Decimal(row.get("net") or (gross - tare))

        # === Додаємо рядок у trips для модалки ===
        trip_info = {
            "document_number": getattr(row["obj"], "document_number", None),
            "date_time": row["date_time"],
            "car": getattr(row["car"], "number", None),
            "driver": getattr(row["driver"], "full_name", None),
            "trailer": getattr(row["trailer"], "number", None),
            "culture": getattr(row["culture"], "name", None),
            "unloading_place": getattr(row["unloading_place"], "name", None),
            "sender": getattr(row.get("sender"), "name", None) if row.get("sender") else None,
            "receiver": getattr(row.get("receiver"), "name", None) if row.get("receiver") else None,
            "gross": float(gross),
            "tare": float(tare),
            "net": float(net),
        }
        totals_by_group_and_culture[group][culture_name]["trips"].append(trip_info)

        # === Агрегування сум ===
        if row["type"] in ("weigher", "arrival"):  # in
            totals_by_group_and_culture[group][culture_name]["gross"] += gross
            totals_by_group_and_culture[group][culture_name]["tare"] += tare
            totals_by_group_and_culture[group][culture_name]["net"] += net

            groups_summary[group]["gross"] += gross
            groups_summary[group]["tare"] += tare
            groups_summary[group]["net"] += net

            totals["gross_in"] += gross
            totals["net_in"] += net

        elif row["type"] == "shipment":  # out
            totals_by_group_and_culture[group][culture_name]["gross"] -= gross
            totals_by_group_and_culture[group][culture_name]["tare"] -= tare
            totals_by_group_and_culture[group][culture_name]["net"] -= net

            groups_summary[group]["gross"] -= gross
            groups_summary[group]["tare"] -= tare
            groups_summary[group]["net"] -= net

            totals["gross_out"] += gross
            totals["net_out"] += net

    # === Формування table_rows ===
    table_rows = []
    for group_key, cultures in totals_by_group_and_culture.items():
        for culture_name, sums in cultures.items():
            table_rows.append({
                "group": group_key,
                "culture": culture_name,
                "gross": float(sums["gross"]),
                "tare": float(sums["tare"]),
                "net": float(sums["net"]),
                "trips": sums["trips"],  # ✅ Тепер доступно в шаблоні
            })

    final_balance = totals["net_in"] - totals["net_out"]

    groups_summary_out = {
        g: {"gross": float(v["gross"]), "tare": float(v["tare"]), "net": float(v["net"])}
        for g, v in groups_summary.items()
    }

    totals_out = {k: float(v) for k, v in totals.items()}
    totals_out["balance"] = float(final_balance)

    return {
        "table_rows": table_rows,
        "groups_summary": groups_summary_out,
        "totals": totals_out,
    }
    

def compute_stock_balance(date_from, date_to, unloading_place=None, culture=None, driver=None, car=None):
    """
    Повертає список рядків з балансом по складах та культурам:
    [
        {
            "place_id": 1,
            "place_name": "Склад А",
            "culture_name": "Пшениця",
            "in_net": Decimal(...),
            "out_net": Decimal(...),
            "balance": Decimal(...),
        }, ...
    ]
    ПРИПУЩЕННЯ:
    - ArrivalJournal та WeigherJournal вважаємо за надходження (in)
    - ShipmentJournal — за відвантаження (out)
    За потреби змінити правила фільтрації тут.
    """

    # загальні фільтри по датах
    date_filters = {
        "date_time__date__gte": date_from,
        "date_time__date__lte": date_to,
    }

    # робимо базові querysets з фільтрами
    arrival_qs = ArrivalJournal.objects.filter(**date_filters)
    weigher_qs = WeigherJournal.objects.filter(**date_filters)
    shipment_qs = ShipmentJournal.objects.filter(**date_filters)

    # опціональні фільтри
    if unloading_place:
        arrival_qs = arrival_qs.filter(unloading_place=unloading_place)
        weigher_qs = weigher_qs.filter(unloading_place=unloading_place)
        shipment_qs = shipment_qs.filter(unloading_place=unloading_place)
    if culture:
        arrival_qs = arrival_qs.filter(culture=culture)
        weigher_qs = weigher_qs.filter(culture=culture)
        shipment_qs = shipment_qs.filter(culture=culture)
    if driver:
        arrival_qs = arrival_qs.filter(driver=driver)
        weigher_qs = weigher_qs.filter(driver=driver)
        shipment_qs = shipment_qs.filter(driver=driver)
    if car:
        arrival_qs = arrival_qs.filter(car=car)
        weigher_qs = weigher_qs.filter(car=car)
        shipment_qs = shipment_qs.filter(car=car)

    # агрегації: групуємо по unloading_place + culture
    arr = arrival_qs.values(
        "unloading_place", "unloading_place__name", "culture__name"
    ).annotate(in_net=Sum("weight_net"))

    wgh = weigher_qs.values(
        "unloading_place", "unloading_place__name", "culture__name"
    ).annotate(in_net=Sum("weight_net"))

    shp = shipment_qs.values(
        "unloading_place", "unloading_place__name", "culture__name"
    ).annotate(out_net=Sum("weight_net"))

    # собираємо у словник по ключу (place_id, culture_name)
    data = defaultdict(lambda: {"in_net": 0, "out_net": 0, "place_name": None, "culture_name": None, "place_id": None})

    for r in arr:
        key = (r["unloading_place"], r["culture__name"] or "Без культури")
        data[key]["in_net"] += r.get("in_net") or 0
        data[key]["place_name"] = r.get("unloading_place__name")
        data[key]["culture_name"] = r.get("culture__name") or "Без культури"
        data[key]["place_id"] = r.get("unloading_place")

    for r in wgh:
        key = (r["unloading_place"], r["culture__name"] or "Без культури")
        data[key]["in_net"] += r.get("in_net") or 0
        data[key]["place_name"] = r.get("unloading_place__name")
        data[key]["culture_name"] = r.get("culture__name") or "Без культури"
        data[key]["place_id"] = r.get("unloading_place")

    for r in shp:
        key = (r["unloading_place"], r["culture__name"] or "Без культури")
        data[key]["out_net"] += r.get("out_net") or 0
        data[key]["place_name"] = r.get("unloading_place__name")
        data[key]["culture_name"] = r.get("culture__name") or "Без культури"
        data[key]["place_id"] = r.get("unloading_place")

    # формуємо список рядків, обчислюємо balance = in - out
    rows = []
    for (place_id, culture_name), vals in data.items():
        in_net = vals["in_net"] or 0
        out_net = vals["out_net"] or 0
        balance = in_net - out_net
        rows.append({
            "place_id": vals["place_id"],
            "place_name": vals["place_name"] or "Без назви",
            "culture": vals["culture_name"],
            "in_net": in_net,
            "out_net": out_net,
            "balance": balance,
        })

    # сортування: за місцем, потім культурою
    rows.sort(key=lambda x: (x["place_name"], x["culture"]))
    return rows