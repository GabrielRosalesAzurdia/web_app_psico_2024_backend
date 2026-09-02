from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from appointments.models import Appointment
from appointments.serializers import (
    AppointmentReadSerializer,
    AppointmentSerializer,
    DoctorSerializer,
)
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

        # ---------------------------------------------------------------
        # RF-19 (soft delete): "eliminar" una cita NO borra su fila (se
        # perderia el historial y las estadisticas), solo pone
        # is_active=False. Este bloque decide, segun la URL, que citas se
        # devuelven. Los parametros llegan en camelCase desde el cliente
        # (?onlyInactive=true) y el middleware camel-case los transforma a
        # snake_case (only_inactive) antes de este punto.
        #
        #   ?onlyInactive=true    -> SOLO las citas desactivadas (papelera)
        #   ?includeInactive=true -> activas + desactivadas (todas)
        #   (sin parametro)       -> por defecto: SOLO las citas activas
        # ---------------------------------------------------------------
        if self.request.query_params.get('only_inactive') == 'true':
            queryset = queryset.filter(is_active=False)
        elif self.request.query_params.get('include_inactive') != 'true':
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
    # RF-19: el detalle (GET/PUT/PATCH/DELETE /api/v1/appointment/<id>/) usa
    # el queryset SIN filtrar por is_active a proposito: asi se puede abrir
    # una cita desactivada y reactivarla (PATCH {"isActive": true}).
    queryset = Appointment.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return AppointmentSerializer
        return AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # RF-19: DELETE no borra la fila (se perderia el historial y las
        # estadisticas). "Soft delete": se marca la cita como inactiva y
        # deja de aparecer en los listados normales, pero sigue en la BD.
        instance.is_active = False
        instance.save()

class AppointmentGetPendingApiView(ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        today = now().date()
        # RF-19: este listado (citas pendientes proximas) nunca debe mostrar
        # citas desactivadas, por eso is_active=True va fijo y aqui no hay
        # parametro para incluirlas.
        return Appointment.objects.filter(
            date__gte=today, status="PENDING", is_active=True
        ).order_by('date')

class DoctorListApiView(ListAPIView):
    # GET /api/v1/appointment/doctors/
    #
    # Alimenta el <select> de "psicologo" del formulario de citas: el
    # campo Appointment.doctor es un FK a User, asi que un "psicologo
    # asignable" no es mas que un usuario del sistema.
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    # Sin paginacion a proposito: el formulario necesita la lista
    # completa de una sola vez para armar el combo (no se navega
    # pagina por pagina).
    pagination_class = None

    def get_queryset(self):
        # is_active=True   -> no ofrecer cuentas dadas de baja.
        # is_superuser=False -> excluye al 'admin' del sistema, que no
        #                       atiende pacientes y no debe aparecer
        #                       como opcion asignable.
        # Orden por nombre para que el combo salga alfabetico.
        return get_user_model().objects.filter(
            is_active=True, is_superuser=False
        ).order_by('first_name', 'last_name')


class AppointmentTodayApiView(ListAPIView):
    serializer_class = AppointmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # RF-19: agenda del dia; se excluyen siempre las citas desactivadas
        # (is_active=True fijo, sin opcion de incluirlas).
        return Appointment.objects.filter(date=now().date(), is_active=True).order_by('hour')
class DashboardTodayApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()
        # RF-19: los contadores del dashboard solo cuentan citas activas;
        # las desactivadas (soft delete) no deben inflar los totales.
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
        # RF-19: is_active=True excluye del gráfico las citas desactivadas
        # (soft delete); lo mismo aplica a "daily_cancelled" mas abajo.
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