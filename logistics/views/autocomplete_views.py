from dal import autocomplete
from ..models import Driver, Car, Trailer, Culture, Place




class CarAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Car.objects.all().order_by('number')
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs

    def create_object(self, text):
        number = text.strip()
        obj, created = Car.objects.get_or_create(number=number)
        return obj

class DriverAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Driver.objects.all().order_by('full_name')
        if self.q:
            qs = qs.filter(full_name__icontains=self.q)
        return qs

    def create_object(self, text):
        full_name = text.strip()
        obj, created = Driver.objects.get_or_create(full_name=full_name)
        return obj

class TrailerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Trailer.objects.all().order_by('number')
        if self.q:
            qs = qs.filter(number__icontains=self.q)
        return qs

    def create_object(self, text):
        number = text.strip()
        obj, created = Trailer.objects.get_or_create(number=number)
        return obj

class CultureAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Culture.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def create_object(self, text):
        name = text.strip()
        obj, created = Culture.objects.get_or_create(name=name)
        return obj

class PlaceAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Place.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def create_object(self, text):
        name = text.strip()
        obj, created = Place.objects.get_or_create(name=name)
        return obj
