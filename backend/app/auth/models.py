from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自訂使用者 model，繼承 Django 內建的 AbstractUser（帳號、密碼、
    email、is_active 這些欄位都已經內建，不用重寫）。

    現在就用自訂 User model 而不是直接用 Django 內建的 User，
    是因為之後（Phase 5）要加 storage_quota_bytes 這類跟業務邏輯
    相關的欄位，如果一開始沒用自訂 model，後面要換會很麻煩
    （需要搬移整個資料庫的使用者資料）。這是 Django 官方文件也
    建議的做法：新專案一律從自訂 User model 開始。
    """

    email = models.EmailField(unique=True)

    # Phase 5 會用到的欄位，先留著，預設值先给一個合理的初始配額（例如 5GB）
    storage_quota_bytes = models.BigIntegerField(default=5 * 1024 * 1024 * 1024)

    def __str__(self):
        return self.username
