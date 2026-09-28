from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model


class AuditLog(models.Model):
    # RNF-03 (B-1): bitacora de auditoria. Cada consulta, creacion,
    # modificacion o exportacion de informacion clinica deja un registro
    # automatico (ver AuditLogMixin). Solo se agregan filas, nunca se
    # editan, y PROTECT evita que borrar un usuario o paciente borre su
    # rastro.
    class ActionTypes(models.TextChoices):
        VIEW = 'VIEW', _('Consulta')
        CREATE = 'CREATE', _('Creacion')
        UPDATE = 'UPDATE', _('Modificacion')
        EXPORT = 'EXPORT', _('Exportacion')

    user = models.ForeignKey(
        get_user_model(), related_name='+', on_delete=models.PROTECT)
    action = models.CharField(max_length=20, choices=ActionTypes.choices)
    patient = models.ForeignKey(
        'patient.Patient', related_name='audit_logs', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} {self.user} {self.action} {self.patient_id}'
