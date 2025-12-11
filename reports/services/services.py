from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from balances.models import Balance, BalanceHistory, BalanceSnapshot
from logistics.models import WeigherJournal, ShipmentJournal, FieldsIncome
from waste.models import Utilization, Recycling
from directory.models import Culture, Place
import csv
from io import StringIO


class ReportService:
    """Сервіс для генерації звітів"""
    
    @staticmethod
    def get_balance_report(date_from=None, date_to=None, filters=None):
        """Звіт по залишках (поточний стан)"""
        queryset = Balance.objects.select_related('place', 'culture').all()
        
        if filters:
            if filters.get('place_id'):
                queryset = queryset.filter(place_id=filters['place_id'])
            if filters.get('culture_id'):
                queryset = queryset.filter(culture_id=filters['culture_id'])
            if filters.get('balance_type'):
                queryset = queryset.filter(balance_type=filters['balance_type'])
        
        data = []
        for balance in queryset:
            data.append({
                'place': balance.place.name,
                'culture': balance.culture.name,
                'type': balance.get_balance_type_display(),
                'quantity': float(balance.quantity),
            })
        
        # Агрегація для графіків
        aggregation = {
            'total_quantity': sum(item['quantity'] for item in data) if data else 0,
            'by_place': {},
            'by_culture': {},
        }
        
        for item in data:
            # По місцях
            if item['place'] not in aggregation['by_place']:
                aggregation['by_place'][item['place']] = 0
            aggregation['by_place'][item['place']] += item['quantity']
            
            # По культурах
            if item['culture'] not in aggregation['by_culture']:
                aggregation['by_culture'][item['culture']] = 0
            aggregation['by_culture'][item['culture']] += item['quantity']
        
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
        }
        
    @staticmethod
    def get_balance_snapshot_data(snapshot, filters=None):
        """
        [FIX] Звіт по залишках на конкретну дату (на основі BalanceSnapshot).
        Помилка, про яку ви повідомили, виправляється цим методом.
        """
        queryset = snapshot.history_records.select_related('place', 'culture').all()
        
        if filters:
            if place_id := filters.get('place_id'):
                queryset = queryset.filter(place_id=place_id)
            if culture_id := filters.get('culture_id'):
                queryset = queryset.filter(culture_id=culture_id)
            if balance_type := filters.get('balance_type'):
                queryset = queryset.filter(balance_type=balance_type)

        data = []
        for history in queryset:
            data.append({
                'place': history.place.name,
                'culture': history.culture.name,
                # Примітка: BalanceHistory не має get_balance_type_display(). 
                # Використовуємо поле 'balance_type', а перетворення має відбуватися 
                # в шаблоні або бути додане до моделі BalanceHistory.
                'type': history.balance_type, 
                'quantity': float(history.quantity),
            })
            
        # Агрегація - аналогічно get_balance_report
        aggregation = {
            'total_quantity': sum(item['quantity'] for item in data) if data else 0,
            'by_place': {},
            'by_culture': {},
        }
        
        for item in data:
            if item['place'] not in aggregation['by_place']:
                aggregation['by_place'][item['place']] = 0
            aggregation['by_place'][item['place']] += item['quantity']
            
            if item['culture'] not in aggregation['by_culture']:
                aggregation['by_culture'][item['culture']] = 0
            aggregation['by_culture'][item['culture']] += item['quantity']
            
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
            'snapshot_date': snapshot.snapshot_date.strftime('%d.%m.%Y'),
        }

    @staticmethod
    def get_balance_period_data(start_snapshot, end_snapshot, filters=None):
        """
        [NEW] Звіт по залишках за період (порівняння двох BalanceSnapshot).
        Потрібен для 'Динаміка залишків' (pdf_balance_period).
        """
        # Отримуємо дані для початкового і кінцевого знімків
        start_data_full = ReportService.get_balance_snapshot_data(start_snapshot, filters)
        end_data_full = ReportService.get_balance_snapshot_data(end_snapshot, filters)
        
        start_map = {}
        # Створюємо унікальний ключ (place, culture, type) -> quantity
        for item in start_data_full['data']:
            key = (item['place'], item['culture'], item['type'])
            start_map[key] = item['quantity']
            
        end_map = {}
        for item in end_data_full['data']:
            key = (item['place'], item['culture'], item['type'])
            end_map[key] = item['quantity']

        # Об'єднуємо всі унікальні ключі
        all_keys = set(start_map.keys()) | set(end_map.keys())
        
        data = []
        total_difference = 0.0
        
        for key in sorted(list(all_keys)):
            place, culture, b_type = key
            start_qty = start_map.get(key, 0.0)
            end_qty = end_map.get(key, 0.0)
            difference = end_qty - start_qty
            
            data.append({
                'place': place,
                'culture': culture,
                'type': b_type,
                'start_quantity': start_qty,
                'end_quantity': end_qty,
                'difference': difference,
            })
            total_difference += difference
            
        # Агрегація
        aggregation = {
            'total_difference': total_difference,
            'total_start': start_data_full['aggregation']['total_quantity'],
            'total_end': end_data_full['aggregation']['total_quantity'],
        }

        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
            'date_from': start_snapshot.snapshot_date.strftime('%d.%m.%Y'),
            'date_to': end_snapshot.snapshot_date.strftime('%d.%m.%Y'),
        }
    
    # ... (інші методи get_waste_report, get_weigher_report)
    
    @staticmethod
    def get_waste_report(date_from=None, date_to=None, filters=None):
        """Звіт по відходах"""
        queryset = Balance.objects.filter(
            balance_type='waste'
        ).select_related('place', 'culture')
        
        if filters:
            if filters.get('place_id'):
                queryset = queryset.filter(place_id=filters['place_id'])
            if filters.get('culture_id'):
                queryset = queryset.filter(culture_id=filters['culture_id'])
        
        data = []
        for balance in queryset:
            data.append({
                'place': balance.place.name,
                'culture': balance.culture.name,
                'quantity': float(balance.quantity),
            })
        
        aggregation = {
            'total_waste': sum(item['quantity'] for item in data) if data else 0,
            'by_place': {},
        }
        
        for item in data:
            if item['place'] not in aggregation['by_place']:
                aggregation['by_place'][item['place']] = 0
            aggregation['by_place'][item['place']] += item['quantity']
        
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
        }
    
    @staticmethod
    def get_weigher_report(date_from=None, date_to=None, filters=None):
        """Звіт по внутрішніх переміщеннях"""
        queryset = WeigherJournal.objects.select_related(
            'from_place', 'to_place', 'culture', 'car', 'driver'
        ).all()
        
        if date_from:
            queryset = queryset.filter(date_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_time__date__lte=date_to)
        
        if filters:
            if filters.get('from_place_id'):
                queryset = queryset.filter(from_place_id=filters['from_place_id'])
            if filters.get('to_place_id'):
                queryset = queryset.filter(to_place_id=filters['to_place_id'])
            if filters.get('culture_id'):
                queryset = queryset.filter(culture_id=filters['culture_id'])
        
        data = []
        for journal in queryset:
            data.append({
                'date': journal.date_time.strftime('%d.%m.%Y'),
                'document': journal.document_number or '—',
                'from_place': journal.from_place.name if journal.from_place else '—',
                'to_place': journal.to_place.name if journal.to_place else '—',
                'culture': journal.culture.name if journal.culture else '—',
                'weight_net': float(journal.weight_net) if journal.weight_net else 0.0,
                'driver': journal.driver.full_name if journal.driver else '—',
                'car': journal.car.number if journal.car else '—',
            })
        
        aggregation = {
            'total_weight': sum(item['weight_net'] for item in data) if data else 0,
            'by_culture': {},
            'by_route': {},
        }
        
        for item in data:
            # По культурах
            culture = item['culture']
            if culture not in aggregation['by_culture']:
                aggregation['by_culture'][culture] = 0
            aggregation['by_culture'][culture] += item['weight_net']
            
            # По маршрутах
            route = f"{item['from_place']} → {item['to_place']}"
            if route not in aggregation['by_route']:
                aggregation['by_route'][route] = 0
            aggregation['by_route'][route] += item['weight_net']
        
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
        }
    
    @staticmethod
    def get_shipment_report(date_from=None, date_to=None, filters=None):
        """Звіт по відвантаженням"""
        queryset = ShipmentJournal.objects.select_related(
            'place_from', 'place_to', 'culture', 'car', 'driver'
        ).all()
        
        if date_from:
            queryset = queryset.filter(date_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_time__date__lte=date_to)
        
        if filters:
            if filters.get('action_type'):
                queryset = queryset.filter(action_type=filters['action_type'])
            if filters.get('culture_id'):
                queryset = queryset.filter(culture_id=filters['culture_id'])
        
        data = []
        for journal in queryset:
            data.append({
                'date': journal.date_time.strftime('%d.%m.%Y'),
                'document': journal.document_number or '—',
                'action_type': journal.get_action_type_display() if journal.action_type else '—',
                'place_from': journal.display_place_from or '—',
                'place_to': journal.display_place_to or '—',
                'culture': journal.culture.name if journal.culture else '—',
                'weight_net': float(journal.weight_net) if journal.weight_net else 0.0,
            })
        
        aggregation = {
            'total_weight': sum(item['weight_net'] for item in data) if data else 0,
            'by_action': {},
            'by_culture': {},
        }
        
        for item in data:
            # По типу дії
            action_type = item['action_type']
            if action_type not in aggregation['by_action']:
                aggregation['by_action'][action_type] = 0
            aggregation['by_action'][action_type] += item['weight_net']
            
            # По культурах
            culture = item['culture']
            if culture not in aggregation['by_culture']:
                aggregation['by_culture'][culture] = 0
            aggregation['by_culture'][culture] += item['weight_net']
        
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
        }
        
    @staticmethod
    def get_shipment_summary_data(date_from=None, date_to=None, filters=None):
        """
        [NEW ALIAS] Псевдонім для get_shipment_report. 
        Використовується в get_total_income_period_data.
        """
        return ReportService.get_shipment_report(date_from, date_to, filters)

    @staticmethod
    def get_fields_report(date_from=None, date_to=None, filters=None):
        """Звіт по надходженням з полів"""
        queryset = FieldsIncome.objects.select_related(
            'field', 'place_to', 'culture', 'car', 'driver'
        ).all()
        
        if date_from:
            queryset = queryset.filter(date_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_time__date__lte=date_to)
        
        if filters:
            if filters.get('field_id'):
                queryset = queryset.filter(field_id=filters['field_id'])
            if filters.get('culture_id'):
                queryset = queryset.filter(culture_id=filters['culture_id'])
        
        data = []
        for journal in queryset:
            data.append({
                'date': journal.date_time.strftime('%d.%m.%Y'),
                'document': journal.document_number or '—',
                'field': journal.field.name if journal.field else '—',
                'place_to': journal.place_to.name if journal.place_to else '—',
                'culture': journal.culture.name if journal.culture else '—',
                'weight_net': float(journal.weight_net) if journal.weight_net else 0.0,
                # Додамо place_from для сумісності з логікою get_total_income_period_data
                'place_from': journal.field.name if journal.field else '—', 
            })
        
        aggregation = {
            'total_weight': sum(item['weight_net'] for item in data) if data else 0,
            'by_field': {},
            'by_culture': {},
        }
        
        for item in data:
            # По полях
            field_name = item['field']
            if field_name not in aggregation['by_field']:
                aggregation['by_field'][field_name] = 0
            aggregation['by_field'][field_name] += item['weight_net']
            
            # По культурах
            culture_name = item['culture']
            if culture_name not in aggregation['by_culture']:
                aggregation['by_culture'][culture_name] = 0
            aggregation['by_culture'][culture_name] += item['weight_net']
        
        return {
            'data': data,
            'aggregation': aggregation,
            'total_rows': len(data),
        }
        
    @staticmethod
    def get_field_income_data(date_from=None, date_to=None, filters=None):
        """
        [NEW ALIAS] Псевдонім для get_fields_report. 
        Використовується в get_total_income_period_data.
        """
        return ReportService.get_fields_report(date_from, date_to, filters)
        
    # ... (решта методів: export_to_csv, get_daily_summary, _aggregate_income_data, get_total_income_period_data)
    
    @staticmethod
    def export_to_csv(data, columns):
        """Експорт даних в CSV"""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        
        for row in data:
            # Фільтруємо тільки потрібні колонки
            filtered_row = {k: v for k, v in row.items() if k in columns}
            writer.writerow(filtered_row)
        
        return output.getvalue()
    
    @staticmethod
    def get_daily_summary(date=None):
        """
        [FIXED] Розширений денний звіт для Dashboard.
        Виправлено TypeError: перетворення Decimal у float.
        """
        if not date:
            date = datetime.now().date()
            
        yesterday = date - timedelta(days=1)
        
        # --- Допоміжна функція для отримання статистики за день ---
        def get_day_stats(target_date):
            # Функція для безпечного отримання float
            def get_safe_sum(queryset):
                val = queryset.aggregate(t=Sum('weight_net'))['t']
                return float(val) if val is not None else 0.0

            # 1. Внутрішні переміщення (Weigher)
            w_qs = WeigherJournal.objects.filter(date_time__date=target_date)
            weigher = {
                'count': w_qs.count(),
                'total': get_safe_sum(w_qs)
            }

            # 2. Відвантаження (Shipment)
            s_qs = ShipmentJournal.objects.filter(date_time__date=target_date)
            # Фільтри (налаштуйте під свої значення action_type в БД)
            s_in_qs = s_qs.filter(Q(action_type='Ввезення') | Q(action_type='income'))
            s_out_qs = s_qs.exclude(Q(action_type='Ввезення') | Q(action_type='income'))
            
            shipment = {
                'in_count': s_in_qs.count(),
                'in_total': get_safe_sum(s_in_qs),
                'out_count': s_out_qs.count(),
                'out_total': get_safe_sum(s_out_qs),
            }

            # 3. Поля (Fields)
            f_qs = FieldsIncome.objects.filter(date_time__date=target_date)
            fields = {
                'count': f_qs.count(),
                'total': get_safe_sum(f_qs)
            }
            
            return weigher, shipment, fields

        # --- 1. Отримуємо дані за сьогодні і вчора ---
        today_weigher, today_shipment, today_fields = get_day_stats(date)
        yest_weigher, yest_shipment, yest_fields = get_day_stats(yesterday)

        # --- 2. Розрахунок трендів (%) ---
        def calc_trend(current, previous):
            # current і previous вже гарантовано float
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100

        trends = {
            'weigher': calc_trend(today_weigher['total'], yest_weigher['total']),
            'shipment_in': calc_trend(today_shipment['in_total'], yest_shipment['in_total']),
            'shipment_out': calc_trend(today_shipment['out_total'], yest_shipment['out_total']),
            'fields': calc_trend(today_fields['total'], yest_fields['total']),
        }

        # --- 3. Генерація даних для графіків (останні 7 днів) ---
        sparkline_data = {
            'dates': [],
            'weigher': [],
            'shipment_in': [],
            'shipment_out': [],
            'fields': []
        }

        for i in range(6, -1, -1):
            d = date - timedelta(days=i)
            w, s, f = get_day_stats(d)
            sparkline_data['dates'].append(d.strftime('%d.%m'))
            sparkline_data['weigher'].append(round(w['total'], 1))
            sparkline_data['shipment_in'].append(round(s['in_total'], 1))
            sparkline_data['shipment_out'].append(round(s['out_total'], 1))
            sparkline_data['fields'].append(round(f['total'], 1))

        # --- 4. Залишки (Balance) ---
        balance_val = Balance.objects.aggregate(t=Sum('quantity'))['t']
        total_balance = float(balance_val) if balance_val is not None else 0.0

        return {
            'date': date.strftime('%d.%m.%Y'),
            'today': {
                'weigher': today_weigher,
                'shipment': today_shipment,
                'fields': today_fields,
                'balance': total_balance
            },
            'trends': trends,
            'sparklines': sparkline_data,
            'grand_total': today_weigher['total'] + today_shipment['in_total'] + today_shipment['out_total'] + today_fields['total']
        }
        
    @staticmethod
    def _aggregate_income_data(data):
        """Допоміжний метод для агрегації списку транзакцій ввезення."""
        agg = {
            'total_weight': sum(item.get('weight_net', 0.0) for item in data),
            'by_culture': {},
            'by_place_from': {},
        }
        for item in data:
            culture = item.get('culture', '—')
            place_from = item.get('place_from', '—')
            weight = item.get('weight_net', 0.0)
            
            agg['by_culture'][culture] = agg['by_culture'].get(culture, 0.0) + weight
            # Використовуємо 'place_from', бо це ввезення (звідки привезли)
            agg['by_place_from'][place_from] = agg['by_place_from'].get(place_from, 0.0) + weight
        
        return agg

    @staticmethod
    def get_total_income_period_data(date_from, date_to, filters=None):
        """
        Отримує дані для звіту 'Прихід зерна (Загальний за період)',
        об'єднуючи надходження з полів та зовнішні ввезення.
        """
        # 1. Дані з полів (використовуємо новий псевдонім)
        field_data_full = ReportService.get_field_income_data(date_from, date_to, filters)
        field_data = field_data_full.get('data', [])
        
        # 2. Дані зовнішнього ввезення (Shipment Summary - лише 'Ввезення')
        # Використовуємо новий псевдонім
        shipment_summary_data_full = ReportService.get_shipment_summary_data(date_from, date_to, filters)
        
        # Фільтруємо лише 'Ввезення' (action_type 'income' або 'Ввезення')
        income_data = [
            item for item in shipment_summary_data_full.get('data', [])
            if item.get('action_type') == 'Ввезення' # Або 'income', залежно від вашої моделі
        ]
        
        # 3. Об'єднання та агрегація
        total_income = field_data + income_data
        total_weight = sum(item.get('weight_net', 0.0) for item in total_income)
        
        # Загальна агрегація по культурах
        by_culture = {}
        for item in total_income:
            culture = item.get('culture', '—')
            weight = item.get('weight_net', 0.0)
            by_culture[culture] = by_culture.get(culture, 0.0) + weight

        report_data = {
            'date_from': date_from.strftime('%d.%m.%Y'),
            'date_to': date_to.strftime('%d.%m.%Y'),
            'total_income': total_income,
            'field_income': field_data,          # Окремо: з полів
            'external_income': income_data,          # Окремо: ввезення
            'aggregation': {
                'total_weight': total_weight,
                'by_culture': by_culture,
                # Використовуємо агрегації з підзвітів
                'field_aggregation': field_data_full.get('aggregation', {'total_weight': 0}),
                'external_aggregation': ReportService._aggregate_income_data(income_data),
            }
        }

        return report_data