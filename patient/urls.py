from django.urls import path


from patient.views import (
    PatientCreateApiView,
    PatientRetrieveApiView,
    PatientListApiView,
    PatientIncompleteFieldsApiView,
    PatientNoteListCreateApiView,
    PatientNoteDestroyApiView,
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
         PatientNoteDestroyApiView.as_view(), name='patient-note-destroy'),
    path('list/', PatientListApiView.as_view(), name='patient-list'),
    path('incomplete/',
         PatientIncompleteFieldsApiView.as_view(),
         name="patient-incomplete"),
]
