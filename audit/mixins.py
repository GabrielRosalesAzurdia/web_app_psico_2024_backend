from audit.models import AuditLog
from patient.models import Patient

# Accion que se registra segun el metodo HTTP. DELETE es modificacion
# porque en el expediente no se borra nada, se anula (RF-28).
_ACTIONS_BY_METHOD = {
    'GET': AuditLog.ActionTypes.VIEW,
    'POST': AuditLog.ActionTypes.CREATE,
    'PUT': AuditLog.ActionTypes.UPDATE,
    'PATCH': AuditLog.ActionTypes.UPDATE,
    'DELETE': AuditLog.ActionTypes.UPDATE,
}


class AuditLogMixin:
    # RNF-03 (B-1): se agrega a las vistas de informacion clinica (todas
    # llevan <patient_id> en la URL). Al terminar cada peticion exitosa
    # guarda en la bitacora usuario, accion, paciente y fecha y hora, sin
    # que la vista tenga que hacer nada. Una vista puede fijar
    # audit_action (por ejemplo EXPORT) en vez de deducirla del metodo.
    audit_action = None

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        action = self.audit_action or _ACTIONS_BY_METHOD.get(request.method)
        patient_id = kwargs.get('patient_id')
        # Solo peticiones exitosas de un usuario autenticado sobre un
        # paciente que existe (un 401/403/404 no es un acceso real).
        if (action and patient_id and response.status_code < 400
                and request.user.is_authenticated
                and Patient.objects.filter(pk=patient_id).exists()):
            AuditLog.objects.create(
                user=request.user, action=action, patient_id=patient_id)
        return response
