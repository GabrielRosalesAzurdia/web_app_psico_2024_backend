from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from audit.models import AuditLog
from business.mixins import BusinessScopedMixin
from audit.serializers import AuditLogSerializer
from psico_auth.permissions import staff_permission


class AuditLogListApiView(BusinessScopedMixin, ListAPIView):
    # GET /api/v1/audit/
    #
    # RNF-03 (B-2): consulta de la bitacora, mas reciente primero
    # (Meta.ordering de AuditLog). Solo para el rol administrador.
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, staff_permission('view_audit_log')]
    pagination_class = None
    queryset = AuditLog.objects.select_related('user', 'patient')
