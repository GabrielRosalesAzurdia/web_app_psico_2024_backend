from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class ExpressAppointment(models.Model):
    # Version simplificada de appointments.Appointment: sin status, sin
    # time_block y sin validacion de horario/fecha (puede registrarse con
    # fecha u hora ya pasada).

    class PlaceType(models.TextChoices):
        CDO = 'CDO', _('CDO')
        SEMILLERO = 'SEMILLERO', _('Semillero')
        OTHER = 'OTHER', _('Otro')

    patient = models.ForeignKey(
        'patient.Patient',
        on_delete=models.PROTECT,
        related_name='express_appointment'
    )
    doctor = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='express_appointment'
    )
    place = models.CharField(
        max_length=50,
        choices=PlaceType.choices,
        default=PlaceType.CDO
    )
    notes = models.TextField(blank=True, default='')
    hour = models.TimeField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # RF-19: mismo criterio de soft delete que Appointment.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.date} - {self.patient} - {self.doctor}'
