from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from activity.models import Activity
from activity.serializers import ActivityReadSerializer, ActivitySerializer
from django.utils.timezone import localdate


class ActivityCreateApiView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ActivityReadSerializer
        return ActivitySerializer

    def get_queryset(self):
        queryset = Activity.objects.all()
        date = self.request.query_params.get('date')
        doctor = self.request.query_params.get('doctor')
        patient = self.request.query_params.get('patient')
        if date:
            queryset = queryset.filter(date=date)
        if doctor:
            queryset = queryset.filter(doctors=doctor)
        if patient:
            queryset = queryset.filter(patients=patient)
        return queryset

class ActivityRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()

    def get_queryset(self):
        queryset = Activity.objects.all()
        date = self.request.query_params.get('date')
        doctor = self.request.query_params.get('doctor')
        if date:
            queryset = queryset.filter(date=date)
        if doctor:
            queryset = queryset.filter(doctors=doctor)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ActivitySerializer
        return ActivityReadSerializer
    permission_classes = [IsAuthenticated]
    
class ActivityGetPendingApiView(ListAPIView):
    serializer_class = ActivityReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Antes "today" era un atributo de clase evaluado una sola vez al
        # importar el modulo (nunca se actualizaba dia a dia), y usaba
        # now().date() en UTC en vez de la fecha local. localdate() calcula
        # "hoy" en cada request y respeta TIME_ZONE=America/Guatemala.
        today = localdate()
        return Activity.objects.filter(date__gte=today, status="PENDING").order_by('date')