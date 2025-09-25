from django.http import JsonResponse
import sys

def get_current_weight(request):
    reader = getattr(sys, "weight_reader", None)
    print(reader, reader.latest_weight if reader else "No reader")
    if reader and reader.latest_weight is not None:
        return JsonResponse({"weight": reader.latest_weight})
    else:
        return JsonResponse({"weight": None})
