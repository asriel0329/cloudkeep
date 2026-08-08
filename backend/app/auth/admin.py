from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    直接沿用 Django 內建的 UserAdmin 介面（帳密管理、權限管理都現成的），
    只多顯示 storage_quota_bytes 這個自訂欄位，方便你在後台一眼看到
    每個使用者的儲存配額。
    """

    list_display = DjangoUserAdmin.list_display + ("storage_quota_bytes",)
