from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from psico_auth.permissions import IsAdministrator


class AuditLogListApiView(ListAPIView):
    # GET /api/v1/audit/
    #
    # RNF-03 (B-2): consulta de la bitacora, mas reciente primero
    # (Meta.ordering de AuditLog). Solo para el rol administrador.
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdministrator]
    pagination_class = None
    queryset = AuditLog.objects.select_related('user', 'patient')
