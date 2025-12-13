"""
Додаткові методи для ReportService
Додайте ці методи до класу ReportService в reports/services.py
"""

@staticmethod
def get_balance_snapshot_data(snapshot, filters=None):
    """
    Отримує дані зі снепшота з фільтрацією
    
    Args:
        snapshot: BalanceSnapshot instance
        filters: dict з фільтрами
    
    Returns:
        dict з даними звіту
    """
    from balances.models import BalanceHistory
    from django.db.models import Sum
    
    queryset = BalanceHistory.objects.filter(
        snapshot=snapshot
    ).select_related('place', 'culture')
    
    if filters:
        if filters.get('place_id'):
            queryset = queryset.filter(place_id=filters['place_id'])
        if filters.get('culture_id'):
            queryset = queryset.filter(culture_id=filters['culture_id'])
        if filters.get('balance_type'):
            queryset = queryset.filter(balance_type=filters['balance_type'])
    
    data = []
    for record in queryset:
        data.append({
            'place': record.place.name,
            'culture': record.culture.name,
            'type': record.get_balance_type_display(),
            'quantity': float(record.quantity),
        })
    
    # Агрегація
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
        'snapshot_date': snapshot.snapshot_date,
    }


@staticmethod
def compare_balance_snapshots(start_snapshot, end_snapshot, filters=None):
    """
    Порівнює два снепшоти для аналізу динаміки
    
    Args:
        start_snapshot: BalanceSnapshot на початок періоду
        end_snapshot: BalanceSnapshot на кінець періоду
        filters: dict з фільтрами
    
    Returns:
        list з даними порівняння
    """
    from balances.models import BalanceHistory
    
    # Отримуємо дані з обох снепшотів
    start_data = {}
    end_data = {}
    
    # Початковий снепшот
    start_records = BalanceHistory.objects.filter(
        snapshot=start_snapshot
    ).select_related('place', 'culture')
    
    if filters:
        if filters.get('place_id'):
            start_records = start_records.filter(place_id=filters['place_id'])
        if filters.get('culture_id'):
            start_records = start_records.filter(culture_id=filters['culture_id'])
    
    for record in start_records:
        key = (record.place_id, record.culture_id, record.balance_type)
        start_data[key] = {
            'place': record.place.name,
            'culture': record.culture.name,
            'type': record.get_balance_type_display(),
            'quantity': float(record.quantity)
        }
    
    # Кінцевий снепшот
    end_records = BalanceHistory.objects.filter(
        snapshot=end_snapshot
    ).select_related('place', 'culture')
    
    if filters:
        if filters.get('place_id'):
            end_records = end_records.filter(place_id=filters['place_id'])
        if filters.get('culture_id'):
            end_records = end_records.filter(culture_id=filters['culture_id'])
    
    for record in end_records:
        key = (record.place_id, record.culture_id, record.balance_type)
        end_data[key] = {
            'place': record.place.name,
            'culture': record.culture.name,
            'type': record.get_balance_type_display(),
            'quantity': float(record.quantity)
        }
    
    # Об'єднуємо дані
    all_keys = set(start_data.keys()) | set(end_data.keys())
    comparison = []
    
    for key in all_keys:
        start_item = start_data.get(key, {})
        end_item = end_data.get(key, {})
        
        start_qty = start_item.get('quantity', 0)
        end_qty = end_item.get('quantity', 0)
        
        # Визначаємо назви (беремо з того, де є)
        place = start_item.get('place') or end_item.get('place', '—')
        culture = start_item.get('culture') or end_item.get('culture', '—')
        
        comparison.append({
            'place': place,
            'culture': culture,
            'start_quantity': start_qty,
            'end_quantity': end_qty,
            'change': end_qty - start_qty,
            'change_percent': ((end_qty - start_qty) / start_qty * 100) if start_qty != 0 else 0
        })
    
    # Сортуємо за абсолютною зміною (спочатку найбільші)
    comparison.sort(key=lambda x: abs(x['change']), reverse=True)
    
    return comparison


@staticmethod
def get_income_by_date(date, filters=None):
    """
    Отримує дані про прихід зерна за конкретну дату
    
    Args:
        date: Дата звіту
        filters: dict з фільтрами
    
    Returns:
        dict з даними звіту
    """
    from logistics.models import FieldsIncome
    from django.db.models import Sum
    
    queryset = FieldsIncome.objects.filter(
        date_time__date=date
    ).select_related('field', 'place_to', 'culture', 'car', 'driver')
    
    if filters:
        if filters.get('field_id'):
            queryset = queryset.filter(field_id=filters['field_id'])
        if filters.get('culture_id'):
            queryset = queryset.filter(culture_id=filters['culture_id'])
        if filters.get('place_to_id'):
            queryset = queryset.filter(place_to_id=filters['place_to_id'])
    
    data = []
    for journal in queryset:
        data.append({
            'date': journal.date_time.strftime('%d.%m.%Y'),
            'time': journal.date_time.strftime('%H:%M'),
            'document': journal.document_number or '—',
            'field': journal.field.name if journal.field else '—',
            'culture': journal.culture.name if journal.culture else '—',
            'place_to': journal.place_to.name if journal.place_to else '—',
            'weight_net': float(journal.weight_net) if journal.weight_net else 0.0,
        })
    
    # Агрегація
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