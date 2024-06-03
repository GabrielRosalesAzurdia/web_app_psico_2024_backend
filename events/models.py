from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
class Events (models.Model): 
    class StatusType(models.TextChoices):
        CDO = 'CDO', _('Cdo')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        OTROS = 'OTROS', _('Otros')
    types=models.TextField()
    date=models.DateField()
    status = models.CharField(
        max_length=50,
        choices=StatusType.choices,
        default=StatusType.CDO)
    doctor = models.ManyToManyField(
        get_user_model(),
        related_name='events'
    )
# Create your models here.
