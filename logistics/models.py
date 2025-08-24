from django.db import models
from directory.models import Car, Trailer, Driver, Culture, Partner, UnloadingPlace


class Trip(models.Model):
    document_number = models.CharField(max_length=50, verbose_name="№ документа / накладної")
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата і час")
    
    sender = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="sent_trips",
        limit_choices_to={"partner_type__in": ["sender", "both"]},
        verbose_name="Відправник"
    )
    receiver = models.ForeignKey(
        Partner,
        on_delete=models.CASCADE,
        related_name="received_trips",
        limit_choices_to={"partner_type__in": ["receiver", "both"]},
        verbose_name="Отримувач"
    )

    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name="Автомобіль")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, verbose_name="Водій")
    trailer = models.ForeignKey(Trailer, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Причеп")
    
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE, verbose_name="Культура")

    weight_gross = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Вага брутто (кг)")
    weight_tare = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Вага тари (кг)")
    weight_net = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="Вага нетто (кг)")

    unloading_place = models.ForeignKey(UnloadingPlace, on_delete=models.CASCADE, verbose_name="Місце розвантаження")
    driver_signature = models.CharField(max_length=255, blank=True, null=True, verbose_name="Підпис водія (електронний)")
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")

    def save(self, *args, **kwargs):
        # Автоматично розраховує нетто = брутто - тара
        self.weight_net = self.weight_gross - self.weight_tare
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Рейс {self.document_number} ({self.culture.name})"
