from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class Appointment(models.Model):

    class StatusType(models.TextChoices):
        DONE = 'DONE', _('Hecho')
        PENDING = 'PENDING', _('Pendiente')
        CANCELLED = 'CANCELLED', _('Cancelado')
    class PlaceType(models.TextChoices):
        CDO = 'CDO', _('CDO')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        OTHER = 'OTHER', _('Otro')

    patient = models.ForeignKey(
        'patient.Patient',
        on_delete=models.PROTECT,
        related_name='appointment'
    )
    place = models.CharField(
        max_length=50,
        choices=PlaceType.choices,
        default=PlaceType.CDO
    )
    notes = models.TextField()
    

    # created_by = models.ForeignKey(
    #     get_user_model(),
    #     on_delete=models.PROTECT,
    #     related_name='appointment'
    # )
    doctor = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='appointment'
    )
    hour = models.TimeField()
    date = models.DateField()
    goal = models.ForeignKey(
        'goals.Goal',
        on_delete=models.PROTECT,
        related_name='goal',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=StatusType.choices,
        default=StatusType.PENDING)

    def __str__(self):
        return f'{self.date} - {self.patient} - {self.doctor}'