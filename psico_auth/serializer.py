from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from dj_rest_auth.registration.serializers import RegisterSerializer

from business.permissions import HasActiveBusiness, get_user_business
from profiles.models import Profile
from psico_auth.enums import GroupName
from psico_auth.permissions import PROFESSIONAL_DEFAULT_PERMISSIONS


class UserRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=25, write_only=True)

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

        # Multi-tenant: la cuenta nueva queda en el negocio del
        # administrador que la crea. Nunca se lee del body.
        business = get_user_business(request.user)
        if business is None:
            raise PermissionDenied(HasActiveBusiness.message)

        # El administrador del negocio crea cuentas de psicologos.
        group, _ = Group.objects.get_or_create(
            name=GroupName.PROFESSIONAL.value)

        user = super().save(request)
        user.groups.add(group)
        # Casillas por defecto de un profesional. (Despues el administrador
        # las va a elegir al crear la cuenta.)
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='psico_auth',
            codename__in=PROFESSIONAL_DEFAULT_PERMISSIONS))
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
