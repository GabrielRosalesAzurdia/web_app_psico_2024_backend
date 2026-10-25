from rest_framework import serializers
from business.serializers import BusinessScopedSerializerMixin
from express_appointment.models import ExpressAppointment
from patient.serializers import PatientSerializer
from psico_auth.serializer import UserSerializer


class ExpressAppointmentSerializer(BusinessScopedSerializerMixin, serializers.ModelSerializer):
    # Multi-tenant: paciente y psicologo solo del negocio de la cuenta.
    business_scoped_fields = {
        'patient': 'business',
        'doctor': 'profile__business',
    }

    class Meta:
        model = ExpressAppointment
        fields = '__all__'


class ExpressAppointmentReadSerializer(ExpressAppointmentSerializer):
    patient = PatientSerializer()
    doctor = UserSerializer()
