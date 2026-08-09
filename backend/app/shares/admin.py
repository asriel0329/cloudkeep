from django.contrib import admin

from .models import Share


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "file", "folder", "permission_level", "expires_at", "created_at"]