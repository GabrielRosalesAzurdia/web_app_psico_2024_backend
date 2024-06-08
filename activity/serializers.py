from rest_framework import serializers

from activity.models import Activity

from psico_auth.serializer import UserSerializer


class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = '__all__'


class ActivityReadSerializer(ActivitySerializer):
    doctor = UserSerializer(many=True)