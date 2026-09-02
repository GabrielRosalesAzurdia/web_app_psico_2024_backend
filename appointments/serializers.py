from rest_framework import serializers
from django.utils.timezone import now
from appointments.models import Appointment

from patient.serializers import PatientSerializer

from psico_auth.serializer import UserSerializer



class DoctorSerializer(serializers.Serializer):
    # Salida del endpoint GET /api/v1/appointment/doctors/.
    #
    # Serializa instancias de User (no hay modelo Psicologo: el campo
    # Appointment.doctor apunta directo a User). Se expone solo lo que
    # el formulario de citas necesita para pintar y enviar el <select>:
    #   - id        -> value de cada <option> (lo que se manda al crear la cita)
    #   - full_name -> texto visible de la opcion
    # username / first_name / last_name / email van incluidos por si el
    # front quiere mostrarlos, pero no son imprescindibles.
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        # User.get_full_name() = "first_name last_name" ya recortado.
        # Si el usuario no tiene nombre cargado, cae al username para no
        # devolver una opcion con texto vacio.
        return obj.get_full_name() or obj.username


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

