from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from business.permissions import HasActiveBusiness
from psico_auth.permissions import IsAdministrator
from psico_auth.serializer import UserRegisterSerializer, UserSerializer


def password_reset_redirect(request, uidb64, token):
    return redirect(f'{settings.FRONTEND_URL}/accounts/password/reset/confirm/{uidb64}/{token}')


class ProfessionalAccountCreateApiView(APIView):
    # POST /api/v1/auth/registration/
    #
    # Multi-tenant: el administrador del negocio crea cuentas de
    # psicologos para SU negocio. No hay registro publico; las cuentas de
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

        return Response(UserSerializer(user).data, status=HTTP_201_CREATED)
