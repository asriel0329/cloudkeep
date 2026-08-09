from django.contrib import admin

from .models import Folder


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "owner", "parent", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name"]
