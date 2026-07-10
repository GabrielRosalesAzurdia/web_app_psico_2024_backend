from django.urls import path
from reports.views import MonthlyReportApiView
from reports.views import MonthlyReportApiView, ReportVerifyApiView
urlpatterns = [
    path('monthly/', MonthlyReportApiView.as_view(), name='report-monthly'),
    path('verify/<str:token>/', ReportVerifyApiView.as_view(), name='report-monthly')
]
