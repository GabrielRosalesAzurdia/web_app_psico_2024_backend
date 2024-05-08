from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _

from rest_framework import serializers

from dj_rest_auth.registration.serializers import RegisterSerializer

from profiles.models import Profile


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

        group, _ = Group.objects.get_or_create(name='client')

        user = super().save(request)
        user.groups.add(group)
        Profile.objects.create(
            user=user,
            phone_number=phone_number)

        return user

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()