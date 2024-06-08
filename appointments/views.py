from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer, AppointmentSerializer
from django.utils.timezone import now


class AppointmentCreateApiView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    # def get_queryset(self):
    #     return Appointment.objects.filter(doctor=self.request.user.pk)

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