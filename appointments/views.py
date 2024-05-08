from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer, AppointmentSerializer


class AppointmentCreateApiView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]


class AppointmentRetrieveApiView(RetrieveUpdateAPIView):
    queryset = Appointment.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return AppointmentSerializer
        return AppointmentReadSerializer
    permission_classes = [IsAuthenticated]