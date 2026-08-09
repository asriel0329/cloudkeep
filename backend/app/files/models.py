from django.conf import settings
from django.db import models

from app.folders.models import Folder


class File(models.Model):
    name = models.CharField(max_length=255)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="files"
    )

    folder = models.ForeignKey(
        Folder,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="files",
        help_text="null 代表這個檔案放在使用者的根目錄。",
    )

    # storage_key 是這個檔案在底層 Storage（Local/S3）裡實際的存放位置，
    # 跟使用者看到的檔名(name)分開，是為了避免檔名衝突、特殊字元問題，
    # 也讓底層儲存的檔案位置跟使用者的操作（改名、搬移）完全脫鉤。
    storage_key = models.CharField(max_length=512, unique=True)

    # SHA-256 hex digest，64 個字元。Phase 1 先存起來，
    # Phase 5 做「去重偵測」時會直接用這個欄位比對。
    hash = models.CharField(max_length=64, db_index=True)

    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "folder", "name"],
                name="unique_file_name_per_folder",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name