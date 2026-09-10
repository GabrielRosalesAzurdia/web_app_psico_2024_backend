from rest_framework import serializers

from appointments.schedule import ScheduleError, resolve_activity_hours
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

    # Opcional: si mandan `time_block`, el horario se deriva del bloque.
    # allow_null=True en ambas (antes solo end_hour la tenia): igual que en
    # AppointmentSerializer, si el cliente manda explicitamente null (en
    # vez de omitir la clave) el campo no debe rechazarlo antes de que
    # validate()/resolve_activity_hours() la derive del bloque.
    start_hour = serializers.TimeField(required=False, allow_null=True)
    end_hour = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = Activity
        fields = '__all__'

    def validate(self, data):
        def current(field):
            if field in data:
                return data[field]
            return getattr(self.instance, field, None)

        time_block = current('time_block')
        try:
            start, end = resolve_activity_hours(
                time_block, current('start_hour'), current('end_hour')
            )
        except ScheduleError as exc:
            raise serializers.ValidationError({exc.field: exc.message})
        data['start_hour'] = start
        data['end_hour'] = end
        return data


class ActivityReadSerializer(ActivitySerializer):
    doctors = UserSerializer(many=True)
    patients = PatientSerializer(many=True, required = False)