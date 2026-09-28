from django.urls import path

from audit.views import AuditLogListApiView

urlpatterns = [
    path('', AuditLogListApiView.as_view(), name='audit-log-list'),
]
