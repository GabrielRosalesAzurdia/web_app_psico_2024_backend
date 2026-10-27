from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from business.mixins import BusinessScopedMixin
from business.permissions import HasActiveBusiness
from psico_auth.models import StaffPermission
from psico_auth.permissions import (
    IsAdministrator,
    is_business_administrator,
    set_staff_permissions,
)
from psico_auth.serializer import (
    StaffPermissionsSerializer,
    StaffSerializer,
    UserRegisterSerializer,
)


def password_reset_redirect(request, uidb64, token):
    return redirect(f'{settings.FRONTEND_URL}/accounts/password/reset/confirm/{uidb64}/{token}')


class ProfessionalAccountCreateApiView(APIView):
    # POST /api/v1/auth/registration/
    #
    # Multi-tenant: el administrador del negocio crea cuentas del
    # personal para SU negocio, con las casillas que marque. No hay registro publico; las cuentas de
    # administradores las crea el superusuario en el admin de Django.
    #
    # No usamos RegisterView de dj_rest_auth porque inicia sesion como el
    # usuario nuevo y devuelve sus tokens: aqui quien llena el formulario
    # es el administrador, no la persona de la cuenta.
    permission_classes = [IsAuthenticated, HasActiveBusiness, IsAdministrator]

    def post(self, request):
        serializer = UserRegisterSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Si algo falla a la mitad (grupo, perfil), no queda un usuario
        # creado a medias.
        with transaction.atomic():
            user = serializer.save(request)

        return Response(StaffSerializer(user).data, status=HTTP_201_CREATED)



class StaffPermissionCatalogApiView(APIView):
    # GET /api/v1/auth/staff/permissions/
    #
    # Las casillas que existen, con su texto, para que el frontend las
    # dibuje sin escribirlas a mano: [{"codename": ..., "name": ...}].
    permission_classes = [IsAuthenticated, HasActiveBusiness, IsAdministrator]

    def get(self, request):
        return Response([
            {'codename': codename, 'name': name}
            for codename, name in StaffPermission._meta.permissions
        ])


class StaffListApiView(BusinessScopedMixin, ListAPIView):
    # GET /api/v1/auth/staff/
    #
    # Cuentas del negocio del administrador, con sus casillas. Incluye a
    # los administradores (isAdministrator=true) para mostrarlos sin
    # poder editarlos.
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    pagination_class = None
    business_lookup = 'profile__business'
    queryset = get_user_model().objects.order_by('first_name', 'last_name', 'username')


class StaffPermissionsUpdateApiView(BusinessScopedMixin, APIView):
    # PATCH /api/v1/auth/staff/<id>/permissions/  {"permissions": [...]}
    #
    # Cambia las casillas de una cuenta del personal. La lista reemplaza
    # a las anteriores. Reglas:
    # - Solo cuentas del mismo negocio (otra -> 404, no se revela que existe).
    # - Nunca la propia cuenta ni la de un administrador (-> 403): esas
    #   solo las cambia el superusuario.
    permission_classes = [IsAuthenticated, IsAdministrator]

    def patch(self, request, pk):
        User = get_user_model()
        user = get_object_or_404(User, pk=pk, profile__business=self.business)
        if user.pk == request.user.pk:
            raise PermissionDenied('No puedes cambiar tus propias casillas.')
        if is_business_administrator(user):
            raise PermissionDenied(
                'Las casillas de un administrador no se pueden cambiar.')

        serializer = StaffPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_staff_permissions(user, serializer.validated_data['permissions'])

        # Se vuelve a leer: Django guarda en cache los permisos del objeto.
        user = User.objects.get(pk=user.pk)
        return Response(StaffSerializer(user).data)
