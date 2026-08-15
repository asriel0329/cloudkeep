from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "action", "target_type", "target_name", "created_at"]
    list_filter = ["action", "target_type"]
    search_fields = ["target_name"]