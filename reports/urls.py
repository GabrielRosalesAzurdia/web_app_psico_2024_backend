from django.urls import path
from reports.views import MonthlyReportApiView, ReportVerifyApiView, MonthlyStatsApiView, ScheduleStatsApiView

urlpatterns = [
    path('monthly/', MonthlyReportApiView.as_view(), name='report-monthly'),
    path('verify/<str:token>/', ReportVerifyApiView.as_view(), name='report-verify'),
    path('monthly-stats/', MonthlyStatsApiView.as_view(), name='report-monthly-stats'),
    path('schedule-stats/', ScheduleStatsApiView.as_view(), name='report-schedule-stats'),
]
