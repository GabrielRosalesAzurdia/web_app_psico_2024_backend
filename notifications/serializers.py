from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    # Solo lectura: los avisos los crea el servidor, nunca el frontend.

    class Meta:
        model = Notification
        fields = ['id', 'kind', 'message', 'appointment',
                  'is_read', 'read_at', 'created_at']
        read_only_fields = fields
