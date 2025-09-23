from django.db.models import Sum, F, Count


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

