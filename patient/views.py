from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, DestroyAPIView
from rest_framework.mixins import UpdateModelMixin
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.generics import get_object_or_404
from patient.models import Patient, PatientNote, CaseReassignment, ConsentTextVersion, PatientConsent
from patient.serializers import PatientSerializer, PatientNoteSerializer, CaseReassignmentSerializer, PatientConsentSerializer
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer
from psico_auth.serializer import UserSerializer
from rest_framework import filters
from rest_framework.views import APIView
from rest_framework.response import Response
from audit.models import AuditLog
from audit.mixins import AuditLogMixin
from io import BytesIO
from xml.sax.saxutils import escape
from django.http import HttpResponse
from django.utils.timezone import localdate
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from psico_auth.permissions import IsProfessional

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


class PatientNoteListCreateApiView(AuditLogMixin, ListCreateAPIView):
    # GET/POST /api/v1/patient/<patient_id>/notes/
    #
    # RF-26: notas clinicas del expediente, independientes de una cita.
    # No hay bloqueo por consentimiento todavia (RF-33 no existe en el
    # sistema); cuando exista, va aca en get_queryset/perform_create.
    serializer_class = PatientNoteSerializer
    permission_classes = [IsAuthenticated, IsProfessional]
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


class PatientNoteDetailApiView(AuditLogMixin, UpdateModelMixin,DestroyAPIView ):
    # DELETE /api/v1/patient/<patient_id>/notes/<pk>/ -> 204 sin cuerpo;
    # 403 si no sos el autor. No estaba en el alcance original de RF-26
    # ("acumulativas, no se borran"), pero hace falta para poder limpiar
    # una nota cargada por error sin dejarla para siempre en el expediente.
    serializer_class = PatientNoteSerializer
    permission_classes = [IsAuthenticated, IsPatientNoteAuthor, IsProfessional]
    queryset = PatientNote.objects.all()
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        serializer.save(edited_by =self.request.user, edited_at=timezone.now())
        
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
class PatientFileApiView(AuditLogMixin, APIView):
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
    permission_classes = [IsAuthenticated, IsProfessional]

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


class PatientConsentDocumentApiView(AuditLogMixin, APIView):
    # GET /api/v1/patient/<patient_id>/consent/document/
    #
    # RF-33 (B-2): genera el PDF del consentimiento informado con los datos
    # del paciente prellenados, usando la version vigente del texto
    # (is_current=True).
    audit_action = AuditLog.ActionTypes.EXPORT
    permission_classes = [IsAuthenticated, IsProfessional]

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)

        text_version = ConsentTextVersion.objects.filter(is_current=True).first()
        if text_version is None:
            return Response(
                {'detail': 'No hay una version vigente del consentimiento.'},
                status=400)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Daniel Padnos Wellness Center", styles['Title']))
        elements.append(Paragraph("Consentimiento informado", styles['Title']))
        elements.append(Paragraph(
            f"Version {escape(text_version.version)} - Generado el {localdate():%d/%m/%Y}",
            styles['Normal']))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Datos del paciente", styles['Heading2']))
        elements.append(Paragraph(f"Nombre: {escape(patient.name)}", styles['Normal']))
        elements.append(Paragraph(f"Edad: {patient.age} años", styles['Normal']))
        if patient.birth_date:
            elements.append(Paragraph(
                f"Fecha de nacimiento: {patient.birth_date:%d/%m/%Y}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Cada bloque del texto separado por una linea en blanco se vuelve
        # un parrafo del PDF.
        for block in text_version.content.split('\n\n'):
            elements.append(Paragraph(
                escape(block).replace('\n', '<br/>'), styles['Normal']))
            elements.append(Spacer(1, 8))
        elements.append(Spacer(1, 40))

        # Menor de edad: autoriza y firma el padre, madre o tutor.
        if patient.age < 18:
            elements.append(Paragraph(
                "Autorizacion del padre, madre o tutor", styles['Heading2']))
            elements.append(Paragraph(
                f"Nombre del tutor: {escape(patient.tutor) or '______________________'}",
                styles['Normal']))
            elements.append(Spacer(1, 30))
            elements.append(Paragraph(
                "Firma del tutor: ______________________", styles['Normal']))
        else:
            elements.append(Paragraph(
                "Firma del paciente: ______________________", styles['Normal']))

        doc.build(elements)
        buffer.seek(0)

        filename = f"consentimiento_{patient.pk}_v{text_version.version}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PatientConsentUploadApiView(AuditLogMixin, APIView):
    # POST /api/v1/patient/<patient_id>/consent/upload/
    #
    # RF-33 (B-3): carga el escaneado del consentimiento firmado (PDF o
    # imagen) en el campo "file" (multipart/form-data). Es opcional: el
    # original queda en fisico y nada se bloquea si no se carga. Queda
    # ligado a la version vigente del texto, y como hay escaneado firmado
    # se marca el check consent_signed del paciente.
    permission_classes = [IsAuthenticated, IsProfessional]
    ALLOWED_CONTENT_TYPES = ['application/pdf', 'image/jpeg', 'image/png']

    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)

        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response({'file': 'Este campo es requerido.'}, status=400)
        if uploaded.content_type not in self.ALLOWED_CONTENT_TYPES:
            return Response(
                {'file': 'Solo se permiten archivos PDF, JPG o PNG.'}, status=400)

        text_version = ConsentTextVersion.objects.filter(is_current=True).first()
        if text_version is None:
            return Response(
                {'detail': 'No hay una version vigente del consentimiento.'},
                status=400)

        consent = PatientConsent.objects.create(
            patient=patient,
            text_version=text_version,
            created_by=request.user,
            uploaded_by=request.user,
            uploaded_at=timezone.now(),
            file_data=uploaded.read(),
            # Sin comillas: rompen el encabezado Content-Disposition al descargar.
            file_name=uploaded.name.replace('"', ''),
            file_content_type=uploaded.content_type,
        )
        patient.consent_signed = True
        patient.save()
        return Response(PatientConsentSerializer(consent).data, status=201)


class PatientConsentFileApiView(AuditLogMixin, APIView):
    # GET /api/v1/patient/<patient_id>/consent/<pk>/file/
    #
    # RF-33 (B-3): descarga el escaneado. Es la unica forma de obtenerlo y
    # exige usuario autenticado, asi el archivo nunca queda en un enlace
    # publico permanente.
    permission_classes = [IsAuthenticated, IsProfessional]

    def get(self, request, patient_id, pk):
        consent = get_object_or_404(
            PatientConsent, pk=pk, patient_id=patient_id)
        if not consent.file_data:
            return Response(
                {'detail': 'Este consentimiento no tiene archivo cargado.'},
                status=404)

        response = HttpResponse(
            bytes(consent.file_data), content_type=consent.file_content_type)
        response['Content-Disposition'] = f'attachment; filename="{consent.file_name}"'
        return response


def _pdf_table(rows, col_widths, header=True):
    # Tabla con bordes para los PDF del expediente. Si header=True la
    # primera fila es el encabezado y se repite en cada pagina.
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    if header:
        style.append(('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey))
    table.setStyle(TableStyle(style))
    return table


class PatientExportApiView(AuditLogMixin, APIView):
    # GET /api/v1/patient/<patient_id>/export/
    #
    # RF-34 (B-1): copia imprimible del expediente completo en PDF: datos
    # generales, notas clinicas, historial de citas y profesionales que
    # atendieron al paciente, con la fecha de generacion y el usuario que
    # lo genero. Usa las mismas consultas que PatientFileApiView (RF-25) y
    # PatientDoctorApiView (RF-30).
    audit_action = AuditLog.ActionTypes.EXPORT
    permission_classes = [IsAuthenticated, IsProfessional]

    def get(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id)

        notes = patient.clinical_notes.filter(is_active=True).select_related('author')
        appointments = Appointment.objects.filter(
            patient=patient, is_active=True
        ).select_related('doctor').order_by('-date', '-hour')
        doctors = get_user_model().objects.filter(
            appointment__patient_id=patient_id,
            appointment__is_active=True,
        ).distinct().order_by('first_name', 'last_name')

        def user_name(user):
            return escape(user.get_full_name() or user.username)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        normal = styles['Normal']
        elements = []

        elements.append(Paragraph("Daniel Padnos Wellness Center", styles['Title']))
        elements.append(Paragraph("Expediente del paciente", styles['Title']))
        elements.append(Paragraph(
            f"Generado el {timezone.localtime():%d/%m/%Y %H:%M} por {user_name(request.user)}",
            normal))
        elements.append(Spacer(1, 20))

        # 1. Datos generales
        elements.append(Paragraph("1. Datos generales", styles['Heading2']))
        general = [
            ('Nombre', patient.name),
            ('Edad', f'{patient.age} años'),
            ('Fecha de nacimiento',
             f'{patient.birth_date:%d/%m/%Y}' if patient.birth_date else ''),
            ('Género', patient.get_gender_display()),
            ('Teléfono', patient.phone),
            ('Dirección', patient.address),
            ('Grado', patient.grade),
            ('Lugar', patient.get_place_display()),
            ('Tutor', patient.tutor),
            ('Teléfono del encargado', patient.managers_phone_number),
            ('Psicólogo asignado',
             (patient.assigned_psychologist.get_full_name()
              or patient.assigned_psychologist.username)
             if patient.assigned_psychologist else ''),
            ('Consentimiento firmado', 'Sí' if patient.consent_signed else 'No'),
        ]
        elements.append(_pdf_table(
            [[Paragraph(f'<b>{label}</b>', normal),
              Paragraph(escape(str(value).strip()) or '-', normal)]
             for label, value in general],
            [2.2 * inch, 4.3 * inch], header=False))
        elements.append(Spacer(1, 20))

        # 2. Notas clinicas (RF-26), la mas reciente primero
        elements.append(Paragraph("2. Notas clínicas", styles['Heading2']))
        if not notes:
            elements.append(Paragraph("Sin notas registradas.", normal))
        for note in notes:
            # La BD guarda las fechas en UTC; localtime las pasa a la hora local.
            created_at = timezone.localtime(note.created_at)
            header = f'<b>{created_at:%d/%m/%Y %H:%M} - {user_name(note.author)}</b>'
            if note.edited_at:
                header += f' (editada el {timezone.localtime(note.edited_at):%d/%m/%Y %H:%M})'
            elements.append(Paragraph(header, normal))
            elements.append(Paragraph(
                escape(note.content).replace('\n', '<br/>'), normal))
            elements.append(Spacer(1, 10))
        elements.append(Spacer(1, 10))

        # 3. Historial de citas (RF-19: solo citas activas)
        elements.append(Paragraph("3. Historial de citas", styles['Heading2']))
        if not appointments:
            elements.append(Paragraph("Sin citas registradas.", normal))
        else:
            rows = [[Paragraph(f'<b>{h}</b>', normal) for h in
                     ('Fecha', 'Hora', 'Profesional', 'Estado', 'Lugar', 'Observaciones')]]
            for appointment in appointments:
                rows.append([
                    Paragraph(f'{appointment.date:%d/%m/%Y}', normal),
                    Paragraph(f'{appointment.hour:%H:%M}', normal),
                    Paragraph(user_name(appointment.doctor), normal),
                    Paragraph(str(appointment.get_status_display()), normal),
                    Paragraph(str(appointment.get_place_display()), normal),
                    Paragraph(escape(appointment.notes).replace('\n', '<br/>'), normal),
                ])
            elements.append(_pdf_table(
                rows, [0.9 * inch, 0.6 * inch, 1.2 * inch,
                       0.85 * inch, 0.85 * inch, 2.1 * inch]))
        elements.append(Spacer(1, 20))

        # 4. Profesionales que lo atendieron (RF-30). KeepTogether evita que
        # el titulo quede solo al final de una pagina y la lista en la otra.
        section = [Paragraph(
            "4. Profesionales que atendieron al paciente", styles['Heading2'])]
        if not doctors:
            section.append(Paragraph("Sin profesionales registrados.", normal))
        for doctor in doctors:
            section.append(Paragraph(f'- {user_name(doctor)}', normal))
        elements.append(KeepTogether(section))

        doc.build(elements)
        buffer.seek(0)

        filename = f"expediente_{patient.pk}_{localdate():%Y%m%d}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
