from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from patient.models import Patient
from patient.serializers import PatientSerializer
from rest_framework import filters


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

