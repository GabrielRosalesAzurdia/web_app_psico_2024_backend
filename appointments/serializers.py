from rest_framework import serializers

from appointments.models import Appointment

from patient.serializers import PatientSerializer

from psico_auth.serializer import UserSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    # created_by = serializers.HiddenField(
    #     default=serializers.CurrentUserDefault()
    # )

    class Meta:
        model = Appointment
        fields = '__all__'


class AppointmentReadSerializer(AppointmentSerializer):
    patient = PatientSerializer()
    doctor = UserSerializer()
    # created_by = UserSerializer()
