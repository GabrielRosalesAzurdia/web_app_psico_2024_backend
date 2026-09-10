from rest_framework import serializers
from django.utils.timezone import localdate
from appointments.models import Appointment
from appointments.schedule import ScheduleError, resolve_hour

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


    # Opcional: si mandan `time_block`, la hora se deriva del bloque.
    # allow_null=True: AppointmentCreateApiView.post() arma el dict con
    # request.data.get('hour') (None explicito cuando no se manda, no
    # ausente), asi que sin allow_null el campo rechazaba "None" antes de
    # que validate()/resolve_hour() llegara a derivarla del bloque.
    hour = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = '__all__'

    def _current(self, data, field):
        if field in data:
            return data[field]
        return getattr(self.instance, field, None)

    def validate(self, data):
        status = data.get('status')
        date = data.get('date')

        if self.instance:
            status = status or self.instance.status
            date = date or self.instance.date
        # localdate() (no now().date()): ver appointments/views.py.
        if date > localdate() and status == 'DONE':
            raise serializers.ValidationError({"status": "No se puede marcar como cumplida una cita futura"})

        # --- Validacion de horario (bloque de 40min u hora libre) ---
        time_block = self._current(data, 'time_block')
        hour = self._current(data, 'hour')
        try:
            data['hour'] = resolve_hour(time_block, hour)
        except ScheduleError as exc:
            raise serializers.ValidationError({exc.field: exc.message})

        # Doble reserva: el mismo psicologo no puede tener dos citas
        # vigentes a la misma fecha y hora.
        doctor = self._current(data, 'doctor')
        if doctor and date:
            clash = Appointment.objects.filter(
                doctor=doctor, date=date, hour=data['hour'], is_active=True
            ).exclude(status=Appointment.StatusType.CANCELLED)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {"hour": "El psicologo ya tiene una cita en ese horario."}
                )
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

