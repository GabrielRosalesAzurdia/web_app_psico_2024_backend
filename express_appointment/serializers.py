from rest_framework import serializers

from express_appointment.models import ExpressAppointment
from patient.serializers import PatientSerializer
from psico_auth.serializer import UserSerializer


class ExpressAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpressAppointment
        fields = '__all__'


class ExpressAppointmentReadSerializer(ExpressAppointmentSerializer):
    patient = PatientSerializer()
    doctor = UserSerializer()
