from django.conf import settings
from django.db import models

from app.folders.models import Folder


class Permission(models.Model):
    """
    掛在資料夾上的權限。查詢某使用者對某資料夾的權限時，
    會往上沿著 parent 一路找，只要「自己或任何一層祖先資料夾」
    有授權，就視為對這個資料夾也有權限——這就是「往下繼承」的意思：
    權限記錄本身掛在上層，但效力會延伸到底下所有子項目。
    """

    READ = "read"
    WRITE = "write"
    LEVEL_CHOICES = [(READ, "唯讀"), (WRITE, "可讀寫")]

    folder = models.ForeignKey(
        Folder, on_delete=models.CASCADE, related_name="permissions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="folder_permissions",
    )
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=READ)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["folder", "user"]

    def __str__(self):
        return f"{self.user} -> {self.folder} ({self.level})"