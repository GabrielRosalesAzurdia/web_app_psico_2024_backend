from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from business.mixins import BusinessScopedMixin
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20


class NotificationListApiView(BusinessScopedMixin, ListAPIView):
    # Issue #145: GET /api/v1/notifications/ -> avisos de la cuenta que
    # pregunta (nunca los de otra persona), no leidos primero.
    # ?unread=true -> solo los no leidos.
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get('unread') == 'true':
            queryset = queryset.filter(is_read=False)
        return queryset


class NotificationUnreadCountApiView(BusinessScopedMixin, APIView):
    # GET /api/v1/notifications/unread-count/ -> {"count": 3}
    # Para el numerito de la campana sin traer toda la lista.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            business=self.business, recipient=request.user, is_read=False).count()
        return Response({'count': count})


class NotificationMarkReadApiView(BusinessScopedMixin, APIView):
    # POST /api/v1/notifications/<pk>/read/ -> marca un aviso como leido.
    # Un aviso de otra persona da 404, como si no existiera.
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = self.get_business_object(
            Notification, pk=pk, recipient=request.user)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadApiView(BusinessScopedMixin, APIView):
    # POST /api/v1/notifications/read-all/ -> marca todos como leidos.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            business=self.business, recipient=request.user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'updated': updated})
