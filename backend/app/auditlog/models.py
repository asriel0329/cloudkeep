from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE_FILE = "delete_file"
    DELETE_FOLDER = "delete_folder"
    CREATE_SHARE = "create_share"
    REVOKE_SHARE = "revoke_share"
    DOWNLOAD_VIA_SHARE = "download_via_share"

    ACTION_CHOICES = [
        (UPLOAD, "上傳檔案"),
        (DOWNLOAD, "下載檔案"),
        (DELETE_FILE, "刪除檔案"),
        (DELETE_FOLDER, "刪除資料夾"),
        (CREATE_SHARE, "建立分享連結"),
        (REVOKE_SHARE, "撤銷分享連結"),
        (DOWNLOAD_VIA_SHARE, "透過分享連結下載"),
    ]

    # user 允許是 null：透過分享連結存取的人不用登入，這種情況下
    # 沒有對應的使用者帳號，但我們還是想記錄「有人用這個分享連結做了什麼」。
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)

    # target_name 是刻意「反正規化」存起來的：如果之後那個檔案/資料夾
    # 被刪除了，log 裡還是能看到「當時操作的是叫什麼名字的東西」，
    # 不會因為原始資料被刪掉，連紀錄本身都失去意義。
    target_type = models.CharField(max_length=20)  # "file" / "folder" / "share"
    target_id = models.IntegerField(null=True, blank=True)
    target_name = models.CharField(max_length=255, blank=True)

    detail = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.action} {self.target_type}:{self.target_id}"