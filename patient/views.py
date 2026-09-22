from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, DestroyAPIView
from rest_framework.mixins import UpdateModelMixin
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404
from patient.models import Patient, PatientNote, CaseReassignment
from patient.serializers import PatientSerializer, PatientNoteSerializer, CaseReassignmentSerializer
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer
from psico_auth.serializer import UserSerializer
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response


def _active_unless_requested(queryset, query_params):
    """RF-19 (soft delete): "eliminar" un paciente NO borra su fila de la base
    de datos (perderiamos el historial de citas), solo pone is_active=False.
    Por eso los listados deben esconder esos pacientes salvo que se pidan
    explicitamente. Esta funcion recibe el queryset "crudo" (todos los
    pacientes) y le aplica el filtro segun lo que venga en la URL.

    Parametros de la URL que entiende (el cliente los manda en camelCase,
    p. ej. ?onlyInactive=true, y el middleware djangorestframework-camel-case
    los convierte a snake_case ANTES de que lleguen aca):

      - onlyInactive=true    -> devuelve SOLO los desactivados (vista "papelera")
      - includeInactive=true -> devuelve activos + desactivados (todos)
      - (ningun parametro)    -> comportamiento por defecto: SOLO los activos
    """
    # Caso 1: "papelera" -> unicamente los que fueron desactivados.
    if query_params.get('only_inactive') == 'true':
        return queryset.filter(is_active=False)
    # Caso 2: se piden todos -> no se filtra nada, pasan activos e inactivos.
    if query_params.get('include_inactive') == 'true':
        return queryset
    # Caso 3 (por defecto): se ocultan los desactivados.
    return queryset.filter(is_active=True)


class PatientCreateApiView(ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # GET /api/v1/patient/  -> lista para el frontend.
        # RF-19: por defecto solo activos; ver _active_unless_requested para
        # los parametros ?includeInactive / ?onlyInactive.
        return _active_unless_requested(Patient.objects.all(), self.request.query_params)

class PatientRetrieveApiView(RetrieveUpdateDestroyAPIView):
    # RF-19: el detalle (GET/PUT/PATCH/DELETE /api/v1/patient/<id>/) usa el
    # queryset SIN filtrar por is_active a proposito: asi se puede abrir un
    # paciente desactivado y volver a activarlo (PATCH {"isActive": true}).
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # RF-19: DELETE no borra la fila (se perderia el historial de citas
        # asociadas y romperia las estadisticas). En su lugar hace un
        # "soft delete": marca el paciente como inactivo. A partir de aca
        # deja de aparecer en los listados normales, pero sigue en la BD.
        instance.is_active = False
        instance.save()

class PatientListApiView(ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields=["name"]

    def get_queryset(self):
        # GET /api/v1/patient/list/?search=<nombre> -> buscador por nombre.
        # RF-19: mismo criterio que el listado principal, se ocultan los
        # pacientes desactivados salvo ?includeInactive / ?onlyInactive.
        return _active_unless_requested(Patient.objects.all(), self.request.query_params)

class PatientIncompleteFieldsApiView(APIView):
    # GET /api/v1/patient/incomplete/
    #
    # Detecta pacientes activos con campos clave sin llenar y los expone
    # como lista de "notificaciones" para que el frontend avise que la
    # ficha esta incompleta. Solo pacientes vigentes (is_active=True).
    permission_classes = [IsAuthenticated]

    # Campos que se consideran obligatorios para una ficha "completa".
    # (label -> como se muestra en la notificacion)
    CAMPOS_REQUERIDOS = {
        'phone': 'Telefono',
        'birth_date': 'Fecha de nacimiento',
        'gender': 'Genero',
        'grade': 'Grado',
        'address': 'Direccion',
        'tutor': 'Encargado',
        'managers_phone_number': 'Telefono del encargado',
    }

    def _falta(self, valor):
        # Vacio real: None, cadena vacia o solo espacios (varios campos
        # tienen default=' ' o default='0').
        if valor is None:
            return True
        texto = str(valor).strip()
        return texto in ('', '0')

    def get(self, request):
        pacientes = Patient.objects.filter(is_active=True).order_by('name')

        incompletos = []
        for p in pacientes:
            faltantes = [
                label
                for campo, label in self.CAMPOS_REQUERIDOS.items()
                if self._falta(getattr(p, campo))
            ]
            if faltantes:
                incompletos.append({
                    'id': p.id,
                    'name': p.name,
                    'missing_fields': faltantes,
                    'missing_count': len(faltantes),
                })

        return Response({
            'total': len(incompletos),
            'patients': incompletos,
        })


class PatientNoteListCreateApiView(ListCreateAPIView):
    # GET/POST /api/v1/patient/<patient_id>/notes/
    #
    # RF-26: notas clinicas del expediente, independientes de una cita.
    # No hay bloqueo por consentimiento todavia (RF-33 no existe en el
    # sistema); cuando exista, va aca en get_queryset/perform_create.
    serializer_class = PatientNoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return PatientNote.objects.filter(
            patient_id=self.kwargs['patient_id'], is_active=True
        ).select_related('author')

    def perform_create(self, serializer):
        patient = get_object_or_404(Patient, pk=self.kwargs['patient_id'])
        serializer.save(patient=patient, author=self.request.user)


class IsPatientNoteAuthor(BasePermission):
    # Igual que IsNoteAuthor en note/views.py (RF-24): se deja que se
    # encuentre el objeto y se responda 403, en vez de filtrar el queryset
    # (que daria 404 en una nota ajena).
    message = 'Solo quien escribio la nota puede borrarla.'

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id


class PatientNoteDetailApiView(UpdateModelMixin,DestroyAPIView ):
    # DELETE /api/v1/patient/<patient_id>/notes/<pk>/ -> 204 sin cuerpo;
    # 403 si no sos el autor. No estaba en el alcance original de RF-26
    # ("acumulativas, no se borran"), pero hace falta para poder limpiar
    # una nota cargada por error sin dejarla para siempre en el expediente.
    serializer_class = PatientNoteSerializer
    permission_classes = [IsAuthenticated, IsPatientNoteAuthor]
    queryset = PatientNote.objects.all()
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        serializer.save(edited_by =self.request.user, edited_at=timezone.now())
        
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
class PatientFileApiView(APIView):
    # GET /api/v1/patient/<patient_id>/file/
    #
    # Ficha unica del paciente: junta en una sola respuesta sus datos
    # generales, sus notas clinicas, su historial de citas y su psicologo
    # asignado, para que el frontend no tenga que pedir cada seccion por
    # separado.
    #
    # Esto solo LEE de PatientNote (lo clinico) y Appointment (la agenda),
    # que ya son modelos y apps separados. Si mas adelante hace falta dar
    # acceso a una seccion sin dar acceso a la otra (por ejemplo, alguien
    # que ve la agenda pero no las notas clinicas), es este metodo el que
    # hay que tocar para armar el dict de forma condicional segun el rol.
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)

        notes = patient.clinical_notes.filter(is_active=True).select_related('author')

        appointments = Appointment.objects.filter(
            patient=patient, is_active=True
        ).select_related('doctor').order_by('-date', '-hour')

        # RF-31: psicologo responsable real del paciente (distinto del
        # doctor de cada cita, RF-20). Se asigna/cambia via
        # PatientReassignApiView, no se calcula de la cita mas reciente.
        assigned_psychologist = patient.assigned_psychologist

        return Response({
            'general': PatientSerializer(patient).data,
            'clinical_notes': PatientNoteSerializer(notes, many=True).data,
            'appointment_history': AppointmentReadSerializer(appointments, many=True).data,
            'assigned_psychologist': (
                UserSerializer(assigned_psychologist).data
                if assigned_psychologist else None
            ),
        })
class PatientDoctorApiView(APIView):
    # GET /api/v1/patient/<patient_id>/doctors/
    #
    # RF-30 (B-2): lista, para un paciente dado, todos los profesionales
    # que lo han atendido (una fila por cita, deduplicada). Es dato
    # historico: si el psicologo asignado cambia (RF-31), las citas viejas
    # conservan su propio doctor y siguen apareciendo aca.
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        get_object_or_404(Patient, pk=patient_id)

        # RF-19: igual que en PatientFileApiView, solo citas activas
        # (una cita desactivada no cuenta como "atencion").
        doctors = get_user_model().objects.filter(
            appointment__patient_id=patient_id,
            appointment__is_active=True,
        ).distinct().order_by('first_name', 'last_name')

        return Response(UserSerializer(doctors, many=True).data)


class PatientReassignApiView(APIView):
    # POST /api/v1/patient/<patient_id>/reassign/
    #
    # RF-31 (B-2): reasigna el psicologo responsable del paciente. El
    # motivo es obligatorio y cada traspaso queda registrado en
    # CaseReassignment antes de tocar Patient.assigned_psychologist, para
    # que nunca pueda cambiar sin dejar rastro en el historial. No toca
    # citas anteriores (RF-30).
    permission_classes = [IsAuthenticated]

    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)

        new_psychologist_id = request.data.get('new_psychologist')
        reason = (request.data.get('reason') or '').strip()

        if not new_psychologist_id:
            return Response(
                {'new_psychologist': 'Este campo es requerido.'}, status=400)
        if not reason:
            return Response(
                {'reason': 'El motivo del traspaso es requerido.'}, status=400)

        new_psychologist = get_object_or_404(
            get_user_model(), pk=new_psychologist_id)

        CaseReassignment.objects.create(
            patient=patient,
            previous_psychologist=patient.assigned_psychologist,
            new_psychologist=new_psychologist,
            reason=reason,
            created_by=request.user,
        )

        patient.assigned_psychologist = new_psychologist
        patient.save()

        return Response(PatientSerializer(patient).data)


class PatientReassignmentHistoryApiView(ListAPIView):
    # GET /api/v1/patient/<patient_id>/reassignments/
    #
    # RF-31 (B-2): historial de traspasos del paciente, mas reciente
    # primero (Meta.ordering de CaseReassignment).
    serializer_class = CaseReassignmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        get_object_or_404(Patient, pk=self.kwargs['patient_id'])
        return CaseReassignment.objects.filter(
            patient_id=self.kwargs['patient_id'])
