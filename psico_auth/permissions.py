from rest_framework.permissions import BasePermission

from psico_auth.enums import GroupName


class IsProfessional(BasePermission):
    # RNF-02 (B-2): solo el rol profesional accede a informacion clinica
    # (notas, observaciones, expediente y consentimientos). Se valida en el
    # servidor en cada peticion; ocultar la seccion en el frontend no basta.
    message = 'Solo el rol profesional puede acceder a informacion clinica.'

    def has_permission(self, request, view):
        return request.user.groups.filter(
            name=GroupName.PROFESSIONAL.value).exists()


class IsAdministrator(BasePermission):
    # RNF-03 (B-2): la bitacora de auditoria solo la consulta el rol
    # administrador.
    message = 'Solo el rol administrador puede consultar la bitacora.'

    def has_permission(self, request, view):
        return request.user.groups.filter(
            name=GroupName.ADMINISTRATOR.value).exists()
