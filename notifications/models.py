from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from business.models import BusinessOwnedModel


class Notification(BusinessOwnedModel):
    # Issue #145: avisos dentro de Tulip para una cuenta del personal (la
    # campana del frontend). Por ahora todos salen de una cita: el paciente
    # la confirma o paga desde su link (#144) o el pago se atrasa (#146).
    # El mensaje es corto y nunca lleva informacion clinica.

    class Kind(models.TextChoices):
        APPOINTMENT_CONFIRMED = 'APPOINTMENT_CONFIRMED', _('Cita confirmada por el paciente')
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Comprobante de pago recibido')
        PAYMENT_OVERDUE = 'PAYMENT_OVERDUE', _('Pago atrasado')

    recipient = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=30, choices=Kind.choices)
    appointment = models.ForeignKey(
        'appointments.Appointment', null=True, blank=True,
        on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # No leidas primero; dentro de cada grupo, la mas reciente primero
        # (-id desempata dos avisos creados en el mismo instante).
        ordering = ['is_read', '-created_at', '-id']

    @classmethod
    def for_appointment(cls, appointment, kind):
        # Crea el aviso para la psicologa asignada a la cita, en el negocio
        # de la cita. Lo usaran los endpoints publicos (#144) y la alerta
        # de pagos atrasados (#146).
        patient = appointment.patient.name
        fecha = appointment.date.strftime('%d/%m/%Y')
        hora = appointment.hour.strftime('%H:%M')
        textos = {
            cls.Kind.APPOINTMENT_CONFIRMED: f'{patient} confirmo su cita del {fecha} a las {hora}.',
            cls.Kind.PAYMENT_RECEIVED: f'{patient} envio el comprobante de pago de su cita del {fecha}.',
            cls.Kind.PAYMENT_OVERDUE: f'El pago de la cita de {patient} del {fecha} sigue pendiente.',
        }
        return cls.objects.create(
            business=appointment.business,
            recipient=appointment.doctor,
            kind=kind,
            appointment=appointment,
            message=textos[kind],
        )

    def __str__(self):
        return f'{self.recipient} - {self.message}'
