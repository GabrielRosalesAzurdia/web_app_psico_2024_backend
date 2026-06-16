from rest_framework import serializers
from django.utils.timezone import now
from appointments.models import Appointment

from patient.serializers import PatientSerializer

from psico_auth.serializer import UserSerializer



class AppointmentSerializer(serializers.ModelSerializer):
    # created_by = serializers.HiddenField(
    #     default=serializers.CurrentUserDefault()
    # )

    #goal = GoalSerializer(required=False)


    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        status = data.get('status')
        date = data.get('date')

        if self.instance:
            status = status or self.instance.status
            date = date or self.instance.date
        if date > now().date() and status == 'DONE':
            raise serializers.ValidationError({"status": "No se puede marcar como cumplida una cita futura"})        
        return data
class AppointmentReadSerializer(AppointmentSerializer):
    patient = PatientSerializer()
    doctor = UserSerializer()
    attendance_status = serializers.SerializerMethodField()

    def get_attendance_status(self, obj):
        mapping = {
            'PENDING':   'PENDIENTE',
            'DONE':      'CUMPLIDA',
            'CANCELLED': 'NO CUMPLIDA',
        }
        return mapping.get(obj.status, obj.status)

