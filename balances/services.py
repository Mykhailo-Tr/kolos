from django.db import transaction
from django.utils import timezone
from .models import Balance, BalanceHistory, BalanceType

class BalanceService:
    """Сервіс для управління залишками зерна та відходів."""

    @staticmethod
    @transaction.atomic
    def adjust_balance(place, culture, balance_type, delta, note=None):
        """
        Змінює залишок.
        :param place: Place instance
        :param culture: Culture instance
        :param balance_type: 'stock' або 'waste'
        :param delta: Decimal (додатне — надходження, від’ємне — відвантаження)
        """
        balance, _ = Balance.objects.get_or_create(
            place=place,
            culture=culture,
            balance_type=balance_type,
            defaults={"quantity": 0}
        )

        new_quantity = balance.quantity + delta
        if new_quantity < 0:
            raise ValueError(
                f"Недостатньо залишку ({balance.place.name} / {balance.culture.name})."
            )

        balance.quantity = new_quantity
        balance.save()

        # Лог в історію
        # BalanceHistory.objects.create(
        #     place_name=place.name,
        #     culture_name=culture.name,
        #     balance_type=balance_type,
        #     quantity=new_quantity,
        #     snapshot_date=timezone.now(),
        # )

        return balance
    

    def get_balance(place, culture, balance_type):
        """Повертає поточний баланс для вказаного місця, культури та типу балансу."""
        try:
            balance = Balance.objects.get(
                place=place,
                culture=culture,
                balance_type=balance_type
            )
            return balance
        except Balance.DoesNotExist:
            return Balance(
                place=place,
                culture=culture,
                balance_type=balance_type,
                quantity=0
            )