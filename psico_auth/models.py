from django.db import models


class StaffPermission(models.Model):
    # Catalogo de casillas que el administrador del negocio puede marcar
    # al crear una cuenta del personal. Cada permiso de aqui es UNA casilla.
    # No tiene tabla: solo existe para que Django cree los permisos.
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('view_clinical_info', 'Ver y escribir información clínica'),
            ('export_patient_file', 'Exportar expediente completo'),
            ('manage_patients', 'Crear y editar pacientes'),
            ('toggle_patient_active', 'Activar y desactivar pacientes'),
            ('reassign_patient', 'Reasignar psicólogo/a'),
            ('manage_appointments', 'Manejar citas'),
            ('view_reports', 'Ver reportes'),
            ('view_audit_log', 'Ver bitácora'),
        ]
