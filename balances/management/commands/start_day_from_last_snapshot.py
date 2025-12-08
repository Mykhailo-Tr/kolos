from django.core.management.base import BaseCommand
from balances.services import BalanceService


class Command(BaseCommand):
    help = 'Оновити або створити поточні Balance на підставі останнього зліпка (snapshots).'

    def add_arguments(self, parser):
        parser.add_argument('--zeros', action='store_true', help='Для існуючих записів, відсутніх у зліпку, встановити 0')

    def handle(self, *args, **options):
        zero = options.get('zeros', False)
        snapshot, created, updated = BalanceService.start_day_from_last_snapshot(copy_missing_as_zero=zero)
        if not snapshot:
            self.stdout.write(self.style.WARNING('Зліпків не знайдено.'))
            return
        self.stdout.write(self.style.SUCCESS(f'Виконано за зліпком {snapshot.id} ({snapshot.snapshot_date}). Created: {created}, Updated: {updated}'))
