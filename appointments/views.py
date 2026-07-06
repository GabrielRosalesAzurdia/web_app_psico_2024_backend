from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer, AppointmentSerializer
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.status import HTTP_201_CREATED
from rest_framework.pagination import PageNumberPagination

class AppointmentPagination(PageNumberPagination):
    page_size = 10
class AppointmentCreateApiView(ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AppointmentPagination
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AppointmentReadSerializer
        return AppointmentSerializer

    def get_queryset(self):
        queryset = Appointment.objects.all()

        patient_id = self.request.query_params.get('patient')
        doctor_id  = self.request.query_params.get('doctor')
        place      = self.request.query_params.get('place')
        date_from  = self.request.query_params.get('date_from')
        date_to    = self.request.query_params.get('date_to')

        if patient_id:
            queryset = queryset.filter(patient=patient_id)
        if doctor_id:
            queryset = queryset.filter(doctor=doctor_id)
        if place:
            queryset = queryset.filter(place=place)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        order = self.request.query_params.get('order', 'desc')
        if order == 'asc':
            queryset = queryset.order_by('date')
        else:
            queryset = queryset.order_by('-date')

        return queryset


    def post(self, request: Request, format=None, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        serializer = serializer_class(data={
            'patient': request.data.get('patient'),
            'doctor': request.data.get('doctor'),
            'hour': request.data.get('hour'),
            'date': request.data.get('date'),
            'status': request.data.get('status'),
            'place': request.data.get('place'),
            'notes': request.data.get("notes")
        })

        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        appointment_data = self.get_serializer(appointment).data

        return Response(appointment_data, status=HTTP_201_CREATED)

class AppointmentRetrieveApiView(RetrieveUpdateAPIView):
    queryset = Appointment.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return AppointmentSerializer
        return AppointmentReadSerializer
    permission_classes = [IsAuthenticated]
    
class AppointmentGetPendingApiView(ListAPIView):
    today = now().date()
    queryset = Appointment.objects.filter(date__gte=today, status="PENDING").order_by('date')
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]
    # def get_queryset(self):
    #     return Appointment.objects.filter(doctor=self.request.user.pk)
class AppointmentTodayApiView(ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(date=now().date()).order_by('hour')
class DashboardTodayApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        citas_hoy = Appointment.objects.filter(date=today)

        pendientes = citas_hoy.filter(status='PENDING')
        serializer = AppointmentReadSerializer(pendientes, many=True)

        return Response({
            'total_today':     citas_hoy.count(),
            'total_pending':   citas_hoy.filter(status='PENDING').count(),
            'total_done':      citas_hoy.filter(status='DONE').count(),
            'total_cancelled': citas_hoy.filter(status='CANCELLED').count(),
            'pending_appointments': serializer.data,
        })