from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from appointments.schedule import TimeBlock
from web_app_psico_2024_backend.encrypted_fields import EncryptedTextField
from business.models import BusinessOwnedModel


class SessionType(BusinessOwnedModel):
    # Issue #143: tarifas de cada negocio por tipo de sesion (ej.
    # "Individual" Q300, "Pareja" Q450). Solo el administrador del negocio
    # las crea o cambia. No se borran: se desactivan, porque las citas
    # viejas siguen apuntando a su tipo de sesion.
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            # Nombre unico dentro del negocio (sin importar mayus/minus).
            models.UniqueConstraint(
                'business',
                Lower('name'),
                name='unique_session_type_name_per_business',
            ),
        ]

    def __str__(self):
        return f'{self.name} (Q{self.price})'


class Appointment(BusinessOwnedModel):

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
    notes = EncryptedTextField(blank=True, default='')
    

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
    # Bloque de 40min (08:00-12:40). Opcional: si queda vacio, `hour` es
    # una "hora libre" escrita a mano.
    time_block = models.CharField(
        max_length=5,
        choices=TimeBlock.choices,
        blank=True,
        default='',
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=50,
        choices=StatusType.choices,
        default=StatusType.PENDING)

    # RF-19: no se permite eliminar citas (se pierde el historial); en vez
    # de borrar la fila, se desactiva. Distinto de "status" (asistencia
    # cumplida/pendiente/cancelada), que sigue siendo un estado que el
    # psicologo elige activamente sobre una cita vigente.
    is_active = models.BooleanField(default=True)

    # Issue #145: cuando el paciente confirmo la cita desde su link (#144).
    # Es un campo aparte y no un valor mas de "status" porque status dice si
    # asistio: una cita confirmada sigue PENDING hasta que se marca cumplida
    # o no cumplida, y asi sigue en pendientes, recordatorios y reportes.
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # RNF-07: cada vez que se guarda una cita (crearla, marcar asistencia,
        # editarla o desactivarla) se recalcula la ultima atencion del
        # paciente. Si la edicion cambio la cita de paciente, se recalcula
        # tambien el anterior, que pudo perder su ultima atencion.
        previous_patient_id = None
        if self.pk:
            previous_patient_id = Appointment.objects.filter(
                pk=self.pk).values_list('patient_id', flat=True).first()
        super().save(*args, **kwargs)
        self.patient.refresh_last_attention_date()
        if previous_patient_id and previous_patient_id != self.patient_id:
            Patient = self._meta.get_field('patient').related_model
            Patient.objects.get(pk=previous_patient_id).refresh_last_attention_date()

    def __str__(self):
        return f'{self.date} - {self.patient} - {self.doctor}'