from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer, AppointmentSerializer
from django.utils.timezone import now
from goals.models import Goal
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED


class AppointmentCreateApiView(ListCreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    # def get_queryset(self):
    #     return Appointment.objects.filter(doctor=self.request.user.pk)

    def post(self, request: Request, format=None, *args, **kwargs):
        try:
            set_goal = Goal.objects.get(start_time__lte=now().date(), end_time__gte=now().date())
        except Goal.DoesNotExist:
            return Response(
                {'message': 'No set goal'},
                status=HTTP_404_NOT_FOUND
            )

        serializer_class = self.get_serializer_class()

        serializer = serializer_class(data={
            'goal': set_goal.pk,
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
    
    # def perform_create(self, serializer):
    #     try:
    #         set_goal = Goal.objects.get(startTime__lte = now().date(), endTime__gte = now().date())
    #         serializer.validated_data['goal'] = set_goal
    #         serializer.save()
    #     except exceptions.ObjectDoesNotExist:
    #         print("entro al except")
    #         return Response(
    #             {'message': 'No set goal'},
    #             status=HTTP_404_NOT_FOUND
    #         )

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