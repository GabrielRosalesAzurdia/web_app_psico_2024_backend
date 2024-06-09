from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class Activity(models.Model):

    class StatusType(models.TextChoices):
        DONE = 'DONE', _('Hecho')
        PENDING = 'PENDING', _('Pendiente')
        CANCELLED = 'CANCELLED', _('Cancelado')

    class PlaceType(models.TextChoices):
        CDO = 'CDO', _('CDO')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        OTHER = 'OTHER', _('Otro')

    doctors = models.ManyToManyField(
        get_user_model(),
        related_name='activity'
    )
    hour = models.TimeField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activity_type = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=StatusType.choices,
        default=StatusType.PENDING)
    place = models.CharField(
        max_length=50,
        choices=PlaceType.choices,
        default=PlaceType.CDO)

    def __str__(self):
        return f'{self.date} - {self.place}'