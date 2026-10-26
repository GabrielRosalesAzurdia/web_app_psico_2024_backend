from rest_framework.permissions import BasePermission

from psico_auth.enums import GroupName


def has_role(user, role):
    # Roles = grupos de Django; una cuenta puede tener varios.
    # El rol dice QUE puede hacer; el negocio (business/permissions.py)
    # dice SOBRE QUE datos.
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=role.value).exists()


class IsProfessional(BasePermission):
    # RNF-02 (B-2): solo el rol profesional accede a informacion clinica
    # (notas, observaciones, expediente y consentimientos). Se valida en el
    # servidor en cada peticion; ocultar la seccion en el frontend no basta.
    message = 'Solo el rol profesional puede acceder a informacion clinica.'

    def has_permission(self, request, view):
        return has_role(request.user, GroupName.PROFESSIONAL)


class IsAdministrator(BasePermission):
    # RNF-03 (B-2) + multi-tenant: acciones de coordinacion del negocio
    # (bitacora, reasignar pacientes, activarlos o desactivarlos).
    message = 'Solo el rol administrador puede realizar esta accion.'

    def has_permission(self, request, view):
        return has_role(request.user, GroupName.ADMINISTRATOR)
