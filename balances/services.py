from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import Balance, BalanceHistory, BalanceSnapshot, BalanceType


class BalanceService:
    """Сервісний шар — операції над залишками і зліпками."""

    @staticmethod
    @transaction.atomic
    def create_snapshot(description: str = '', created_by: str = 'система', at_time=None) -> BalanceSnapshot:
        """Створити зліпок поточних `Balance`.

        - `at_time` дозволяє вказати довільну дату для зліпка (ручне створення за минулу дату).
        """
        if at_time is None:
            at_time = timezone.now()

        snapshot = BalanceSnapshot.objects.create(snapshot_date=at_time, description=description, created_by=created_by)

        balances = Balance.objects.select_related('place', 'culture').all()
        history_objs = [
            BalanceHistory(
                snapshot=snapshot,
                place=b.place,
                culture=b.culture,
                balance_type=b.balance_type,
                quantity=b.quantity,
            )
            for b in balances
        ]
        BalanceHistory.objects.bulk_create(history_objs)
        return snapshot

    @staticmethod
    @transaction.atomic
    def create_snapshot_from_iterable(rows, description: str = '', created_by: str = 'система', at_time=None) -> BalanceSnapshot:
        """Створює зліпок з переданого переліку dict-рядків: [{'place': place, 'culture': culture, 'balance_type':..., 'quantity': Decimal}, ...]
        Використовується для ручного додавання залишків за минулу дату.
        """
        if at_time is None:
            at_time = timezone.now()

        snapshot = BalanceSnapshot.objects.create(snapshot_date=at_time, description=description, created_by=created_by)
        objs = []
        for r in rows:
            objs.append(BalanceHistory(
                snapshot=snapshot,
                place=r['place'],
                culture=r['culture'],
                balance_type=r.get('balance_type', BalanceType.STOCK),
                quantity=r.get('quantity', Decimal('0')),
            ))
        BalanceHistory.objects.bulk_create(objs)
        return snapshot

    @staticmethod
    @transaction.atomic
    def adjust_balance(place, culture, balance_type, delta):
        """Змінює поточний `Balance.quantity` на delta (Decimal)."""
        balance, _ = Balance.objects.get_or_create(
            place=place,
            culture=culture,
            balance_type=balance_type,
            defaults={'quantity': 0}
        )
        new_q = balance.quantity + delta
        if new_q < 0:
            raise ValueError('Недостатньо залишку.')
        balance.quantity = new_q
        balance.save()
        return balance

    @staticmethod
    def set_balance(place, culture, balance_type, quantity):
        balance, _ = Balance.objects.get_or_create(
            place=place,
            culture=culture,
            balance_type=balance_type,
            defaults={'quantity': 0}
        )
        balance.quantity = quantity
        balance.save()
        return balance

    @staticmethod
    def get_balance(place, culture, balance_type):
        try:
            return Balance.objects.get(place=place, culture=culture, balance_type=balance_type)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def start_day_from_last_snapshot(copy_missing_as_zero: bool = False):
        """Оновлює/створює поточні Balance на підставі останнього зліпка.

        - Якщо `copy_missing_as_zero=True`, то для комбінацій, яких немає в зліпку, створюються записи з 0.
        - Повертає кортеж (snapshot, created_count, updated_count)
        """
        last = BalanceSnapshot.objects.order_by('-snapshot_date').first()
        if not last:
            return None, 0, 0

        # створимо тимчасну мапу (place_id, culture_id, balance_type) -> quantity
        from django.db.models import Q
        keys = {}
        for h in last.history_records.all():
            keys[(h.place_id, h.culture_id, h.balance_type)] = h.quantity

        created = 0
        updated = 0
        # оновимо існуючі balances
        balances = Balance.objects.all()
        for b in balances:
            k = (b.place_id, b.culture_id, b.balance_type)
            if k in keys:
                q = keys.pop(k)
                if b.quantity != q:
                    b.quantity = q
                    b.save()
                    updated += 1
            else:
                if copy_missing_as_zero:
                    if b.quantity != 0:
                        b.quantity = 0
                        b.save()
                        updated += 1

        # створимо решту, які є у зліпку, але немає в поточних balance
        for (place_id, culture_id, btype), qty in keys.items():
            Balance.objects.create(
                place_id=place_id,
                culture_id=culture_id,
                balance_type=btype,
                quantity=qty
            )
            created += 1

        return last, created, updated