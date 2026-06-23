from rest_framework import serializers

from activity.models import Activity
from patient.models import Patient
from patient.serializers import PatientSerializer
from psico_auth.serializer import UserSerializer


class ActivitySerializer(serializers.ModelSerializer):
    patients = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Patient.objects.all(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Activity
        fields = '__all__'


class ActivityReadSerializer(ActivitySerializer):
    doctors = UserSerializer(many=True)
    patients = PatientSerializer(many=True, required = False)