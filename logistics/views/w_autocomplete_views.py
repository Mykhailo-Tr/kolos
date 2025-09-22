from dal import autocomplete
from ..models import Driver, Car, Trailer, Culture, UnloadingPlace, Partner

class SenderAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Partner.objects.filter(partner_type__in=['sender', 'both']).order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def create_object(self, text):
        # Take the text up to " (" if the user input includes additional info.
        name = text.split(' (')[0].strip()
        # Try to get or create the Partner by name.
        obj, created = Partner.objects.get_or_create(name=name)
        # Ensure the partner_type includes 'sender'.
        if created:
            obj.partner_type = 'sender'
            obj.save()
        elif obj.partner_type == 'receiver':
            obj.partner_type = 'both'
            obj.save()
        return obj

class ReceiverAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Partner.objects.filter(partner_type__in=['receiver', 'both']).order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def create_object(self, text):
        name = text.split(' (')[0].strip()
        obj, created = Partner.objects.get_or_create(name=name)
        if created:
            obj.partner_type = 'receiver'
            obj.save()
        elif obj.partner_type == 'sender':
            obj.partner_type = 'both'
            obj.save()
        return obj

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

class UnloadingPlaceAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = UnloadingPlace.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def create_object(self, text):
        name = text.strip()
        obj, created = UnloadingPlace.objects.get_or_create(name=name)
        return obj
