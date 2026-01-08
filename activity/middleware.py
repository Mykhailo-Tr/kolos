import json
from django.utils import timezone
from .models import ActivityLog
from directory.models import Driver, Car, Trailer, Culture, Place, Field
from logistics.models import WeigherJournal, ShipmentJournal, FieldsIncome
from waste.models.recycling import Recycling
from waste.models.utilization import Utilization
from balances.models import Balance, BalanceSnapshot
from datetime import timedelta, datetime
from activity.translations import MODEL_MAPPING

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if len(request.path.strip('/').split('/')) > 1:
            app_url = request.path.strip('/').split('/')[1]
            app_url_shr = request.path.strip('/').split('/')[0]
            action_type_url = request.path.strip('/').split('/')[-1]
        else:
            app_url = None
            action_type_url = None
        pre_info = None

        if request.user.is_authenticated:
            if action_type_url == 'delete':
                if app_url == 'drivers':
                    pre_info = Driver.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'cars':
                    pre_info = Car.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'trailers':
                    pre_info = Trailer.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'cultures':
                    pre_info = Culture.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'places':
                    pre_info = Place.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'fields':
                    pre_info = Field.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'weigher_journals':
                    pre_info = WeigherJournal.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'shipment_journals':
                    pre_info = ShipmentJournal.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'fields_income':
                    pre_info = FieldsIncome.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'recycling':
                    pre_info = Recycling.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'utilization':
                    pre_info = Utilization.objects.filter(id=request.path.strip('/').split('/')[2]).first()
                elif app_url == 'history':
                    pre_info = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
                    pre_info = BalanceSnapshot.objects.filter(id=request.path.strip('/').split('/')[2]).values_list('snapshot_date', flat=True).first()
                    pre_info = (pre_info + timedelta(hours=2)).strftime("%d.%m.%Y %H:%M")
                elif app_url_shr == 'balances':
                    pre_info = Balance.objects.filter(id=request.path.strip('/').split('/')[1]).first()


        response = self.get_response(request)
        

        if request.user.is_authenticated and request.method == "POST":
            # Перевіряємо успішність дії (зазвичай редирект 302 після збереження)
            if response.status_code == 302:

                reqPOST = request.POST.dict()

                description = ""

                path_clear = request.path.strip('/').split('/')

                if path_clear[0] == 'directory' or path_clear[0] == 'logistics' or path_clear[0] == 'waste' or path_clear[0] == 'balances':
                    if path_clear[0] != 'balances':
                        reqPOST['model'] = path_clear[1][:-1].capitalize()
                    elif path_clear[1] == 'history':
                        reqPOST['model'] = 'balance_history'
                        if 'edit' not in path_clear:
                            reqPOST['new_snapshot_date'] = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        reqPOST['model'] = path_clear[0][:-1].capitalize()
                    raw_model_name = reqPOST['model'].lower()
                    description += f"{MODEL_MAPPING.get(raw_model_name, raw_model_name)}: "

                    if action_type_url == 'delete':
                        pre_info = f"{MODEL_MAPPING.get(raw_model_name, raw_model_name)}: {pre_info}"

                    for key in reqPOST:

                        if key not in ['csrfmiddlewaretoken', 'model'] and reqPOST[key] != '':
                            if app_url_shr == 'directory' and key not in ['default_driver', 'parent']:
                                raw_data = key
                                if key == 'place_type':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {MODEL_MAPPING.get(reqPOST[key], reqPOST[key])}; "
                                else:
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}; "

                            elif app_url_shr == 'logistics' and key not in ['date_time', 'driver', 'car', 'trailer', 'culture', 'field', 'place_to', 'place_from','gross_unit', 'tare_unit', 'loss_unit', 'from_place', 'to_place']:
                                raw_data = key
                                if key == 'weight_gross':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['gross_unit']}; "
                                elif key == 'weight_tare':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['tare_unit']}; "
                                elif key == 'weight_loss':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['loss_unit']}; "
                                elif key == 'action_type':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {MODEL_MAPPING.get(reqPOST[key], reqPOST[key])}; "
                                else:
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}; "

                            elif app_url_shr == 'waste' and key not in ['date_time', 'place_to', 'input_unit', 'output_unit']:
                                raw_data = key
                                if key == 'input_quantity' or key == 'quantity':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['input_unit']}; "
                                elif key == 'output_quantity':
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['output_unit']}; "
                                else:
                                    description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}; "
                            elif app_url_shr == 'balances':
                                if app_url != 'history' and key not in ['unit']:
                                    raw_data = key
                                    if key == 'place':
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {Place.objects.filter(id=reqPOST[key]).first()}; "
                                    elif key == 'culture':
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {Culture.objects.filter(id=reqPOST[key]).first()}; "
                                    elif key == 'quantity':
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}{reqPOST['unit']}; "
                                    elif key == 'balance_type':
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {MODEL_MAPPING.get(reqPOST[key], reqPOST[key])}; "
                                    else:
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}; "
                                elif app_url == 'history' and key in ['new_snapshot_date', 'initial-snapshot_date', 'description']:
                                    raw_data = key
                                    if key == 'initial-snapshot_date':
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {((datetime.fromisoformat(reqPOST[key]) + timedelta(hours=2)).strftime("%d.%m.%Y %H:%M"))}; "
                                    else:
                                        description += f"{MODEL_MAPPING.get(raw_data, raw_data)}: {reqPOST[key]}; "

                if 'edit' in request.path.strip('/').split('/'):
                    action_type = "update"
                elif 'delete' in request.path.strip('/').split('/'):
                    action_type = "delete"
                    description = pre_info
                else:
                    action_type = "create"

                if path_clear[0] in ['directory', 'logistics', 'waste', 'balances']:
                    
                    ActivityLog.objects.create(
                        user=request.user,
                        action=action_type,
                        description=description
                    )

        return response