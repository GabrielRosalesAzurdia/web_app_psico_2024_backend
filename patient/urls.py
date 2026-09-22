from django.urls import path


from patient.views import (
    PatientCreateApiView,
    PatientRetrieveApiView,
    PatientListApiView,
    PatientIncompleteFieldsApiView,
    PatientNoteListCreateApiView,
    PatientNoteDetailApiView,
    PatientFileApiView,
    PatientDoctorApiView,
)

urlpatterns = [
    path('',
         PatientCreateApiView.as_view(),
         name='patient-create'),
    path('<int:pk>/',
         PatientRetrieveApiView.as_view(), name='patient-detail'),
    path('<int:patient_id>/notes/',
         PatientNoteListCreateApiView.as_view(), name='patient-notes'),
    path('<int:patient_id>/notes/<int:pk>/',
         PatientNoteDetailApiView.as_view(), name='patient-note-destroy'),
    path('<int:patient_id>/file/',
         PatientFileApiView.as_view(), name='patient-file'),
    path('<int:patient_id>/doctors/',
         PatientDoctorApiView.as_view(), name='patient-doctors'),
    path('list/', PatientListApiView.as_view(), name='patient-list'),
    path('incomplete/',
         PatientIncompleteFieldsApiView.as_view(),
         name="patient-incomplete"),
]
