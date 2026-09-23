from django.urls import path
from reports.views import MonthlyReportApiView, ReportVerifyApiView, MonthlyStatsApiView, ScheduleStatsApiView, PsychologistPatientsApiView, PatientDoctorsApiView

urlpatterns = [
    path('monthly/', MonthlyReportApiView.as_view(), name='report-monthly'),
    path('verify/<str:token>/', ReportVerifyApiView.as_view(), name='report-verify'),
    path('monthly-stats/', MonthlyStatsApiView.as_view(), name='report-monthly-stats'),
    path('schedule-stats/', ScheduleStatsApiView.as_view(), name='report-schedule-stats'),
    path('traceability/psychologist-patient/', PsychologistPatientsApiView.as_view(), name='report-traceability-psychologist-patients'),
      path('traceability/patient-doctors/<int:patient_id>/', PatientDoctorsApiView.as_view(), name='report-traceability-patient-doctors'),
]
