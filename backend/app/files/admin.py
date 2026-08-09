from django.contrib import admin

from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "folder", "size", "mime_type", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name", "hash"]