from django.contrib.auth import get_user_model
from rest_framework import serializers

from psico_auth.permissions import get_staff_permissions


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='profile.phone_number', required=False)
    image = serializers.ImageField(source='profile.image', required=False)
    group = serializers.SerializerMethodField(read_only=True)
    roles = serializers.SerializerMethodField(read_only=True)
    business_name = serializers.SerializerMethodField(read_only=True)
    permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'image',
            'group',
            'roles',
            'business_name',
            'permissions',
        ]

        extra_kwargs = {
            'username': {'read_only': True},
            'email': {'read_only': True},
        }

    @staticmethod
    def get_group(obj) -> str:
        return obj.groups.first().name if obj.groups.first() else None

    @staticmethod 
    def get_roles(obj) -> list[str]:
        # RNF-02 (B-1): todos los roles del usuario, para que el frontend
        # muestre u oculte secciones. "group" se queda por compatibilidad.

        return [group.name for group in obj.groups.all()]

    @staticmethod
    def get_business_name(obj) -> str | None:
        # Multi-tenant: nombre del negocio de la cuenta, para mostrarlo en
        # el encabezado del frontend. Solo lectura: el negocio lo asigna
        # el superusuario en el admin, nunca se cambia desde aqui.
        profile = getattr(obj, 'profile', None)
        business = getattr(profile, 'business', None)
        return business.name if business else None

    @staticmethod
    def get_permissions(obj) -> list[str]:
        # Casillas marcadas en la cuenta (o en su grupo), ej.
        # ["view_clinical_info", "manage_appointments"]. El frontend las usa
        # solo para mostrar u ocultar; el backend las vuelve a revisar.
        return get_staff_permissions(obj)

    @staticmethod
    def update_profile(instance, data):
        phone_number = data.get('phone_number', None)
        if phone_number is not None:
            instance.profile.phone_number = phone_number

        image = data.get('image', None)
        if image is not None:
            instance.profile.image = image

        instance.profile.save()

    def update(self, instance, validated_data):
        profile = validated_data.pop('profile', {})
        if bool(profile):
            self.update_profile(instance, profile)

        return super().update(instance, validated_data)
