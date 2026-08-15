from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "target_type", "target_id",
            "target_name", "detail", "created_at",
        ]