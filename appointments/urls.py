from django.urls import path

from appointments.views import (
    AppointmentCreateApiView,
    AppointmentRetrieveApiView,
    AppointmentGetPendingApiView,
    AppointmentTodayApiView,
    DashboardTodayApiView,
    DoctorListApiView,
)

urlpatterns = [
    path('',
         AppointmentCreateApiView.as_view(),
         name='appointment-create'),
    # Va ANTES de '<int:pk>/' para que Django no intente matchear
    # "doctors" como un id de cita. Lista los psicologos asignables
    # en el formulario de citas (campo doctor).
    path('doctors/',
         DoctorListApiView.as_view(),
         name='appointment-doctors'),
    path('pending/',
         AppointmentGetPendingApiView.as_view(),
         name='appointment-pending'),
    path('<int:pk>/',
         AppointmentRetrieveApiView.as_view(), name='appointment-detail'),
    path('today/',
         AppointmentTodayApiView.as_view(),
         name='appointment-today'),
    path('dashboard/today/',
         DashboardTodayApiView.as_view(),
         name='dashboard-today'),
]
