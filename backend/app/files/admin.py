from django.contrib import admin

from .models import Blob, File, FileVersion


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "folder", "blob_size", "mime_type", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name"]

    def blob_size(self, obj):
        return obj.blob.size
    blob_size.short_description = "大小"


@admin.register(Blob)
class BlobAdmin(admin.ModelAdmin):
    list_display = ["id", "hash", "size", "reference_count", "processing_status", "created_at"]
    search_fields = ["hash"]

@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    list_display = ["id", "file", "version_number", "blob", "created_by", "created_at"]