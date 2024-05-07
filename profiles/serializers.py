from django.contrib.auth import get_user_model
from rest_framework import serializers


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='profile.phone_number', required=False)
    image = serializers.ImageField(source='profile.image', required=False)
    group = serializers.SerializerMethodField(read_only=True)

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
        ]

        extra_kwargs = {
            'username': {'read_only': True},
            'email': {'read_only': True},
        }

    @staticmethod
    def get_group(obj) -> str:
        return obj.groups.first().name if obj.groups.first() else None

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
