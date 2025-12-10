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
        """Звіт по залишках"""
        # Для балансу дати можуть не використовуватись, бо це поточний стан
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
        """Денний звіт - загальна інформація за день"""
        if not date:
            date = datetime.now().date()
        
        # Внутрішні переміщення
        weigher_count = WeigherJournal.objects.filter(
            date_time__date=date
        ).count()
        weigher_total = WeigherJournal.objects.filter(
            date_time__date=date
        ).aggregate(total=Sum('weight_net'))['total'] or 0
        
        # Відвантаження
        shipment_count = ShipmentJournal.objects.filter(
            date_time__date=date
        ).count()
        shipment_total = ShipmentJournal.objects.filter(
            date_time__date=date
        ).aggregate(total=Sum('weight_net'))['total'] or 0
        
        # Надходження з полів
        fields_count = FieldsIncome.objects.filter(
            date_time__date=date
        ).count()
        fields_total = FieldsIncome.objects.filter(
            date_time__date=date
        ).aggregate(total=Sum('weight_net'))['total'] or 0
        
        return {
            'date': date.strftime('%d.%m.%Y'),
            'weigher': {
                'count': weigher_count,
                'total': float(weigher_total),
            },
            'shipment': {
                'count': shipment_count,
                'total': float(shipment_total),
            },
            'fields': {
                'count': fields_count,
                'total': float(fields_total),
            },
            'grand_total': float(weigher_total + shipment_total + fields_total),
        }