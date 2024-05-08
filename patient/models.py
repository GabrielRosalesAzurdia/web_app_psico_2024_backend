from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

class Patient(models.Model):

    class PlaceTypes(models.TextChoices):
        CDO = 'CDO', _('CDO')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        EXTERNAL = 'EXTERNAL', _('Externo')

    name = models.TextField()
    phone = models.CharField(max_length=25, blank=True, default='')
    age = models.IntegerField()
    place = models.CharField(
        max_length=50,
        choices=PlaceTypes.choices,
        default=PlaceTypes.CDO)
    pacientNumber = models.IntegerField(blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    grade = models.TextField(blank=True,default='')
    state = models.BooleanField()
    stateDescription =models.TextField(blank=True, default='')

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='patient'
    )