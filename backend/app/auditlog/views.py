from rest_framework import generics

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    """GET /api/auditlog/ —— 只能看到自己的操作紀錄，最多回傳最近 100 筆"""

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)[:100]