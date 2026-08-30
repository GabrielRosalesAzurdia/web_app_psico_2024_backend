from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from patient.models import Patient
from patient.serializers import PatientSerializer
from rest_framework import filters


def _active_unless_requested(queryset, query_params):
    # RF-19: por defecto solo se listan pacientes activos; ?includeInactive=true
    # (via camelCase middleware llega como include_inactive) trae tambien los
    # desactivados, para poder verlos/reactivarlos sin perder el historial.
    if query_params.get('include_inactive') == 'true':
        return queryset
    return queryset.filter(is_active=True)


class PatientCreateApiView(ListCreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return _active_unless_requested(Patient.objects.all(), self.request.query_params)

class PatientRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # RF-19: no se elimina la fila (se perderia el historial de citas
        # asociadas); se desactiva.
        instance.is_active = False
        instance.save()

class PatientListApiView(ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields=["name"]

    def get_queryset(self):
        return _active_unless_requested(Patient.objects.all(), self.request.query_params)

