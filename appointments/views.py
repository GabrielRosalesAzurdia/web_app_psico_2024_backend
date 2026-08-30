from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from appointments.models import Appointment
from appointments.serializers import AppointmentReadSerializer, AppointmentSerializer
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.status import HTTP_201_CREATED
from rest_framework.pagination import PageNumberPagination
from django.db.models.functions import TruncDay
from django.db.models import Count
from datetime import date as date_type

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

        # RF-19: por defecto solo se listan citas activas; ?includeInactive=true
        # (llega como include_inactive) trae tambien las desactivadas.
        if self.request.query_params.get('include_inactive') != 'true':
            queryset = queryset.filter(is_active=True)

        patient_id = self.request.query_params.get('patient')
        doctor_id  = self.request.query_params.get('doctor')
        place      = self.request.query_params.get('place')
        date_from  = self.request.query_params.get('date_from')
        date_to    = self.request.query_params.get('date_to')
        status  = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

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
            'notes': request.data.get("notes") or ""
        })

        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        appointment_data = self.get_serializer(appointment).data

        return Response(appointment_data, status=HTTP_201_CREATED)

class AppointmentRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return AppointmentSerializer
        return AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # RF-19: no se elimina la fila (se perderia el historial); se
        # desactiva, igual que Patient.
        instance.is_active = False
        instance.save()
    
class AppointmentGetPendingApiView(ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        today = now().date()
        return Appointment.objects.filter(
            date__gte=today, status="PENDING", is_active=True
        ).order_by('date')
class AppointmentTodayApiView(ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(date=now().date(), is_active=True).order_by('hour')
class DashboardTodayApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        citas_hoy = Appointment.objects.filter(date=today, is_active=True)

        pendientes = citas_hoy.filter(status='PENDING')
        serializer = AppointmentReadSerializer(pendientes, many=True)

        return Response({
            'total_today':     citas_hoy.count(),
            'total_pending':   citas_hoy.filter(status='PENDING').count(),
            'total_done':      citas_hoy.filter(status='DONE').count(),
            'total_cancelled': citas_hoy.filter(status='CANCELLED').count(),
            'pending_appointments': serializer.data,
        })

class DashboardMonthlyProgressApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()

        # Primer día de hace 2 meses para traer 3 meses en total
        m = today.month - 2
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        three_months_ago = date_type(y, m, 1)

        # Primer día del mes siguiente como límite superior
        nm = today.month + 1
        ny = today.year
        if nm > 12:
            nm = 1
            ny += 1
        next_month_start = date_type(ny, nm, 1)

        # Citas cumplidas por día, para los últimos 3 meses completos (antes
        # solo traía el día a día del mes actual; los meses anteriores se
        # repartían parejo entre las 4 semanas en el frontend -total/4-, sin
        # reflejar en qué semana realmente hubo más o menos citas. También
        # antes no filtraba por status: mezclaba pendientes/canceladas/
        # cumplidas bajo el nombre "Cumplidas" del gráfico del dashboard).
        daily = (
            Appointment.objects
            .filter(date__gte=three_months_ago, date__lt=next_month_start, status='DONE', is_active=True)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        current_month = [
            {"date": str(entry['day']), "count": entry['count']}
            for entry in daily
        ]

        # Citas canceladas por día del mes actual (línea aparte del gráfico,
        # no se compara entre meses). Antes esta clave ni siquiera se
        # enviaba: la línea "Canceladas" del dashboard quedaba en cero.
        daily_cancelled = (
            Appointment.objects
            .filter(date__year=today.year, date__month=today.month, status='CANCELLED', is_active=True)
            .annotate(day=TruncDay('date'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        current_month_cancelled = [
            {"date": str(entry['day']), "count": entry['count']}
            for entry in daily_cancelled
        ]

        return Response({
            "current_month": current_month,
            "current_month_cancelled": current_month_cancelled,
        })