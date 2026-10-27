from rest_framework.permissions import SAFE_METHODS, BasePermission

from psico_auth.enums import GroupName
from psico_auth.models import StaffPermission


# Casillas que recibe por defecto una cuenta nueva creada desde
# /auth/registration/ (lo que antes daba el rol profesional).
PROFESSIONAL_DEFAULT_PERMISSIONS = [
    'view_clinical_info',
    'export_patient_file',
    'manage_patients',
    'manage_appointments',
    'view_reports',
]


def has_role(user, role):
    # Roles = grupos de Django. Desde las casillas solo queda en uso el
    # grupo administrador: es quien crea cuentas, y su grupo tiene todas
    # las casillas. El negocio (business/permissions.py) dice SOBRE QUE datos.
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=role.value).exists()


class IsAdministrator(BasePermission):
    # Multi-tenant: solo el administrador del negocio crea cuentas del
    # personal. No es una casilla a proposito: si lo fuera, cualquiera con
    # ella podria crear cuentas con mas permisos que los suyos.
    message = 'Solo el rol administrador puede realizar esta accion.'

    def has_permission(self, request, view):
        return has_role(request.user, GroupName.ADMINISTRATOR)


def has_staff_permission(user, codename):
    # True si la casilla esta marcada en la cuenta o en uno de sus grupos.
    if not user or not user.is_authenticated:
        return False
    return user.has_perm(f'psico_auth.{codename}')


def get_staff_permissions(user):
    # Lista de casillas que tiene la cuenta (para el frontend).
    return [
        codename
        for codename, _ in StaffPermission._meta.permissions
        if has_staff_permission(user, codename)
    ]


def staff_permission(codename, writes_only=False):
    # Casillas del personal (psico_auth.StaffPermission): devuelve una clase
    # de permiso de DRF que exige esa casilla marcada en la cuenta (o en
    # su grupo, ej. administrador).
    # writes_only=True: GET sigue abierto para todos y la casilla solo se
    # exige para crear, editar o desactivar (POST/PUT/PATCH/DELETE).
    class HasStaffPermission(BasePermission):
        message = 'No tienes permiso para realizar esta accion.'

        def has_permission(self, request, view):
            if writes_only and request.method in SAFE_METHODS:
                return True
            return has_staff_permission(request.user, codename)

    return HasStaffPermission
