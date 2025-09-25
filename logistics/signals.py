from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ArrivalJournal, ShipmentJournal, WeigherJournal, StockBalance


def update_balance(place, culture, delta):
    """Оновлює залишок (додає або віднімає)"""
    balance, created = StockBalance.objects.get_or_create(
        unloading_place=place,
        culture=culture,
        defaults={"quantity": 0}
    )
    balance.quantity = balance.quantity + delta
    balance.save()


@receiver(post_save, sender=ArrivalJournal)
def arrival_balance_update(sender, instance, created, **kwargs):
    if created:
        update_balance(instance.unloading_place, instance.culture, instance.weight_net)


@receiver(post_save, sender=ShipmentJournal)
def shipment_balance_update(sender, instance, created, **kwargs):
    if created:
        update_balance(instance.unloading_place, instance.culture, -instance.weight_net)


@receiver(post_save, sender=WeigherJournal)
def weigher_balance_update(sender, instance, created, **kwargs):
    if created:
        update_balance(instance.unloading_place, instance.culture, instance.weight_net)
