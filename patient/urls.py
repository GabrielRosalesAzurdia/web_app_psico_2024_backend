from django.urls import path


from patient.views import (
    PatientCreateApiView,
    PatientRetrieveApiView,
    PatientListApiView,
    PatientIncompleteFieldsApiView,
    PatientNoteListCreateApiView,
)

urlpatterns = [
    path('',
         PatientCreateApiView.as_view(),
         name='patient-create'),
    path('<int:pk>/',
         PatientRetrieveApiView.as_view(), name='patient-detail'),
    path('<int:patient_id>/notes/',
         PatientNoteListCreateApiView.as_view(), name='patient-notes'),
    path('list/', PatientListApiView.as_view(), name='patient-list'),
    path('incomplete/',
         PatientIncompleteFieldsApiView.as_view(),
         name="patient-incomplete"),
]
