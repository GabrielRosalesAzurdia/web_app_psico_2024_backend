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

    def validate(self, data):
        start_hour = data.get('start_hour', getattr(self.instance, 'start_hour', None))
        end_hour = data.get('end_hour', getattr(self.instance, 'end_hour', None))
        if not end_hour:
            raise serializers.ValidationError(
                {"end_hour": "La hora de fin es obligatoria."}
            )
        if start_hour and end_hour <= start_hour:
            raise serializers.ValidationError(
                {"end_hour": "La hora de fin debe ser posterior a la hora de inicio."}
            )
        return data


class ActivityReadSerializer(ActivitySerializer):
    doctors = UserSerializer(many=True)
    patients = PatientSerializer(many=True, required = False)