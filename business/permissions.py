from rest_framework.permissions import BasePermission


def get_user_business(user):
    # Multi-tenant: el negocio de la cuenta que hace la peticion. Es la
    # UNICA fuente del negocio; nunca se lee del body ni de la URL.
    # Devuelve None si no hay sesion, si la cuenta no tiene negocio
    # (ej. el superusuario) o si el negocio esta desactivado.
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, 'profile', None)
    business = getattr(profile, 'business', None)
    if business is None or not business.is_active:
        return None
    return business


class HasActiveBusiness(BasePermission):
    # Multi-tenant: solo entra quien pertenece a un negocio activo.
    # Una cuenta sin negocio o de un negocio suspendido recibe 403.
    message = 'Tu cuenta no tiene un negocio activo asignado.'

    def has_permission(self, request, view):
        return get_user_business(request.user) is not None
