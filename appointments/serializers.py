from rest_framework import serializers

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

