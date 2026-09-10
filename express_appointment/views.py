from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.pagination import PageNumberPagination

from express_appointment.models import ExpressAppointment
from express_appointment.serializers import (
    ExpressAppointmentReadSerializer,
    ExpressAppointmentSerializer,
)


class ExpressAppointmentPagination(PageNumberPagination):
    page_size = 10


class ExpressAppointmentListCreateApiView(ListCreateAPIView):
    serializer_class = ExpressAppointmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ExpressAppointmentPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ExpressAppointmentReadSerializer
        return ExpressAppointmentSerializer

    def get_queryset(self):
        queryset = ExpressAppointment.objects.all()

        # RF-19 (soft delete), mismo patron que appointments/views.py.
        if self.request.query_params.get('only_inactive') == 'true':
            queryset = queryset.filter(is_active=False)
        elif self.request.query_params.get('include_inactive') != 'true':
            queryset = queryset.filter(is_active=True)

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
            'place': request.data.get('place'),
            'notes': request.data.get('notes') or ''
        })

        serializer.is_valid(raise_exception=True)
        express_appointment = serializer.save()
        express_appointment_data = self.get_serializer(express_appointment).data

        return Response(express_appointment_data, status=HTTP_201_CREATED)


class ExpressAppointmentRetrieveApiView(RetrieveUpdateDestroyAPIView):
    # Igual que AppointmentRetrieveApiView: queryset SIN filtrar por
    # is_active para poder reactivar una cita express desactivada.
    queryset = ExpressAppointment.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ExpressAppointmentSerializer
        return ExpressAppointmentReadSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
