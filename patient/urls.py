from django.urls import path


from patient.views import (
    PatientCreateApiView,
    PatientRetrieveApiView,
    PatientListApiView,
    PatientIncompleteFieldsApiView,
)

urlpatterns = [
    path('',
         PatientCreateApiView.as_view(),
         name='patient-create'),
    path('<int:pk>/',
         PatientRetrieveApiView.as_view(), name='patient-detail'),
    path('list/', PatientListApiView.as_view(), name='patient-list'),
    path('incomplete/',
         PatientIncompleteFieldsApiView.as_view(),
         name="patient-incomplete"),
]
