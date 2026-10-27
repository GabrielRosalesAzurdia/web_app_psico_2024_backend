from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from dj_rest_auth.registration.serializers import RegisterSerializer

from business.permissions import HasActiveBusiness, get_user_business
from profiles.models import Profile
from psico_auth.permissions import (
    PROFESSIONAL_DEFAULT_PERMISSIONS,
    STAFF_PERMISSION_CODENAMES,
    get_staff_permissions,
    is_business_administrator,
    set_staff_permissions,
)


def permissions_field(**kwargs):
    # Lista de casillas. ChoiceField solo acepta codigos del catalogo:
    # cualquier otro (ej. "change_user") da 400.
    return serializers.ListField(
        child=serializers.ChoiceField(choices=STAFF_PERMISSION_CODENAMES),
        **kwargs)


class UserRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=25, write_only=True)
    # Casillas que el administrador marca al crear la cuenta. Si no se
    # manda, la cuenta recibe las de un profesional.
    permissions = permissions_field(required=False, write_only=True)

    def validate_email(self, email: str):
        already_user = get_user_model().objects \
            .filter(email__exact=email.strip()) \
            .exists()

        if already_user:
            raise serializers.ValidationError(
                _('A user is already registered with this e-mail address.'))

        return super().validate_email(email)

    def get_cleaned_data(self):
        return {
            **super().get_cleaned_data(),

            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }

    def save(self, request):
        phone_number = self.validated_data.pop('phone_number')
        codenames = self.validated_data.pop(
            'permissions', PROFESSIONAL_DEFAULT_PERMISSIONS)

        # Multi-tenant: la cuenta nueva queda en el negocio del
        # administrador que la crea. Nunca se lee del body.
        business = get_user_business(request.user)
        if business is None:
            raise PermissionDenied(HasActiveBusiness.message)

        # Sin grupos: lo que puede hacer la cuenta lo dicen sus casillas.
        # Nunca queda como administrador (eso solo lo hace el superusuario).
        user = super().save(request)
        set_staff_permissions(user, codenames)
        # profiles/signals.py ya crea un Profile vacio en el post_save del
        # User (get_or_create); usar create() aca duplicaba la fila y
        # rompia el registro con IntegrityError (UNIQUE user_id).
        Profile.objects.update_or_create(
            user=user,
            defaults={'phone_number': phone_number, 'business': business})

        return user


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()


class StaffSerializer(serializers.ModelSerializer):
    # Cuenta del personal con sus casillas, para la pantalla del
    # administrador del negocio.
    is_administrator = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_administrator',
            'permissions',
        ]

    @staticmethod
    def get_is_administrator(obj) -> bool:
        # El frontend lo usa para mostrar sus casillas sin poder cambiarlas.
        return is_business_administrator(obj)

    @staticmethod
    def get_permissions(obj) -> list[str]:
        return get_staff_permissions(obj)


class StaffPermissionsSerializer(serializers.Serializer):
    # PATCH de las casillas: la lista reemplaza todas las anteriores.
    permissions = permissions_field(allow_empty=True)
