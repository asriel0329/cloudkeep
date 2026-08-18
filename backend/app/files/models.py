import uuid

from django.conf import settings
from django.db import models

from app.folders.models import Folder


class Blob(models.Model):
    """
    檔案的「實際內容」，跟使用者看到的檔名/資料夾完全脫鉤。
    多個 File 可以指向同一個 Blob——這就是去重偵測的核心：
    hash 一樣，代表內容一模一樣，底層 Storage 只需要真的存一份。
    """

    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "處理中"),
        (STATUS_DONE, "完成"),
        (STATUS_FAILED, "失敗"),
    ]

    hash = models.CharField(max_length=64, unique=True, db_index=True)
    storage_key = models.CharField(max_length=512, unique=True)
    size = models.BigIntegerField()

    thumbnail_key = models.CharField(max_length=512, default="", blank=True)
    processing_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    # 有幾個 File 正在指著這份內容。歸零時代表沒有任何檔案還在用它，
    # 這時候才能真的把 Storage 裡的實際內容清掉，不然會刪到還有人在用的東西。
    reference_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"blob:{self.hash[:8]}... (refs={self.reference_count})"


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

    blob = models.ForeignKey(
        Blob,
        on_delete=models.PROTECT,
        related_name="files",
   )

    # mime_type 保留在 File 上（不是 Blob）：這是上傳當下瀏覽器宣告的類型，
    # 理論上同內容的 mime_type 應該一樣，但保留在 File 上比較不會牽動太多
    # 既有程式碼，风险較低。
    mime_type = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "folder", "name"],
                condition=models.Q(is_deleted=False),
                name="unique_file_name_per_folder",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

class FileVersion(models.Model):
    """
    File 的歷史版本紀錄。每次上傳同名檔案覆蓋，就會多一筆版本，
    File.blob 永遠指向「目前」的版本，但這裡保留完整歷史，
    可以下載或還原成任何一個舊版本。
    """

    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="versions")
    blob = models.ForeignKey(Blob, on_delete=models.PROTECT, related_name="file_versions")
    version_number = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        unique_together = ["file", "version_number"]
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.file.name} v{self.version_number}"

class UploadSession(models.Model):
    """
    大檔案分塊上傳的「工作階段」。前端把檔案切成好幾塊，
    每上傳一塊就記錄進 received_chunks，全部到齊後才組裝、
    走正式的去重/版本控制流程產生真正的 File。

    斷線重連時，前端可以查詢這個 session 的 received_chunks，
    只補傳缺的部分，不用整個檔案重傳。
    """

    STATUS_UPLOADING = "uploading"
    STATUS_ASSEMBLING = "assembling"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_UPLOADING, "上傳中"),
        (STATUS_ASSEMBLING, "組裝中"),
        (STATUS_COMPLETED, "完成"),
        (STATUS_FAILED, "失敗"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="upload_sessions"
    )
    folder = models.ForeignKey(
        Folder, null=True, blank=True, on_delete=models.CASCADE, related_name="upload_sessions"
    )

    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255, default="application/octet-stream")

    total_size = models.BigIntegerField()
    chunk_size = models.BigIntegerField(default=5 * 1024 * 1024)  # 預設每塊 5MB
    total_chunks = models.PositiveIntegerField()

    # 已收到的分塊編號列表，例如 [0, 1, 3]（代表 2 號還沒收到）
    received_chunks = models.JSONField(default=list)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UPLOADING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"upload:{self.filename} ({self.status})"