from django.urls import path


from patient.views import (
    PatientCreateApiView,
    PatientRetrieveApiView
)

urlpatterns = [
    path('',
         PatientCreateApiView.as_view(),
         name='patient-create'),
    path('<int:pk>/',
         PatientRetrieveApiView.as_view(), name='patient-detail'),
]
