from django.urls import path


from appointments.views import (
    AppointmentCreateApiView,
    AppointmentRetrieveApiView
)

urlpatterns = [
    path('',
         AppointmentCreateApiView.as_view(),
         name='appointment-create'),
    path('today/',
         AppointmentCreateApiView.as_view(),
         name='appointment-today'),
    path('<int:pk>/',
         AppointmentRetrieveApiView.as_view(), name='appointment-detail'),
]
