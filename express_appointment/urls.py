from django.urls import path

from express_appointment.views import (
    ExpressAppointmentListCreateApiView,
    ExpressAppointmentRetrieveApiView,
)

urlpatterns = [
    path('',
         ExpressAppointmentListCreateApiView.as_view(),
         name='express-appointment-create'),
    path('<int:pk>/',
         ExpressAppointmentRetrieveApiView.as_view(),
         name='express-appointment-detail'),
]
