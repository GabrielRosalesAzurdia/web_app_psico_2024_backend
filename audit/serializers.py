from rest_framework import serializers

from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient.name')

    class Meta:
        model = AuditLog
        fields = ['id', 'user_name', 'action', 'patient', 'patient_name', 'created_at']
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
