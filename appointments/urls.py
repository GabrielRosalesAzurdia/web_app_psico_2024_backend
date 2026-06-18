from django.urls import path


from appointments.views import (
    AppointmentCreateApiView,
    AppointmentRetrieveApiView,
    AppointmentGetPendingApiView,
    AppointmentTodayApiView
)

urlpatterns = [
    path('',
         AppointmentCreateApiView.as_view(),
         name='appointment-create'),
    path('pending/',
         AppointmentGetPendingApiView.as_view(),
         name='appointment-pending'),
    path('<int:pk>/',
         AppointmentRetrieveApiView.as_view(), name='appointment-detail'),
    path('today/',
         AppointmentTodayApiView.as_view(),
         name='appointment-today'),
]
