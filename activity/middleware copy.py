import json
from django.utils import timezone
from .models import ActivityLog
from directory.models import Driver, Car, Trailer, Culture, Place, Field
from logistics.models import WeigherJournal, ShipmentJournal, FieldsIncome
from waste.models.recycling import Recycling
from waste.models.utilization import Utilization
from balances.models import Balance

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
            if action_type_url == 'delete' or action_type_url == 'edit':
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
                elif app_url_shr == 'balances':
                    pre_info = Balance.objects.filter(id=request.path.strip('/').split('/')[1]).first()


        response = self.get_response(request)
        

        if request.user.is_authenticated and request.method == "POST":
            # Перевіряємо успішність дії (зазвичай редирект 302 після збереження)
            if response.status_code in [200, 302]:
                
                if app_url == 'drivers':              
                    object_name = request.POST.get('full_name')
                    category = ["driver", "водія"]
                elif app_url == 'cars':
                    object_name = request.POST.get('number')
                    category = ["car", "автомобіль"]
                elif app_url == "trailers":
                    object_name = request.POST.get('number')
                    category = ["trailer", "причеп"]
                elif app_url == "cultures":
                    object_name = request.POST.get('name')
                    category = ["culture", "культуру"]
                elif app_url == "places":
                    object_name = request.POST.get('name')
                    category = ["place", "місце"]
                elif app_url == "fields":
                    object_name = request.POST.get('name')
                    category = ["field", "поле"]
                elif app_url_shr == "logistics":
                    object_name = request.POST.get('document_number') + '; ' + request.POST.get('initial-date_time')
                    category = ["document", "документ"]
                elif app_url_shr == "waste":
                    object_name = request.POST.get('initial-date_time')
                    if app_url == "recycling":
                        category = ["recycling", "переробку"]
                    else:
                        category = ["utilization", "утилізацію"]
                elif app_url == "history":
                    object_name = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
                    category = ["snapshot", "зліпок"]
                elif app_url_shr == "balances":
                    if action_type_url == "create":
                        object_name = str(request.POST.get('quantity')) + str(request.POST.get('unit'))

                        if request.POST.get('balance_type') == "waste":
                            object_name += " відходів "
                        else:
                            object_name += " зерна "

                        object_name += f"'{str(Culture.objects.get(pk=request.POST.get('culture')).name)}' "     
                        
                        object_name += f"в '{str(Place.objects.get(pk=request.POST.get('place')).name)}'"
                    else:
                        object_name = None

                    category = ["balance", "залишок"]
                else:
                    object_name = None
                    category = ["object", "об'єкт"]

                path = request.path.lower()

                if "add" in path or "create" in path:
                    action_type = ["create", "створив"]
                elif "delete" in path:
                    action_type = ["delete", "видалив"]
                else:
                    action_type = ["update", "оновив"]

                if "edit" in path:
                    description = f"Користувач {request.user.username} {action_type[1]} {category[1]}: {pre_info}"
                elif "delete" in path:
                    description = f"Користувач {request.user.username} {action_type[1]} {category[1]}: {pre_info}"
                else:
                    description = f"Користувач {request.user.username} {action_type[1]} {category[1]}: {object_name}"
                
                ActivityLog.objects.create(
                    user=request.user,
                    action=action_type[0],
                    description=description
                )

        return response