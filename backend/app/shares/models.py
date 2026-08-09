import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from app.files.models import File
from app.folders.models import Folder


def generate_token():
    # token_urlsafe 產生的字串夠長、夠隨機，猜中的機率低到可忽略，
    # 適合用來當「拿著這串就等於有權限」的分享連結金鑰。
    return secrets.token_urlsafe(24)


class Share(models.Model):
    READ = "read"
    WRITE = "write"
    LEVEL_CHOICES = [(READ, "唯讀"), (WRITE, "可讀寫")]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shares"
    )

    # 只會有一個不是 null：分享的是檔案，或是分享的是資料夾
    file = models.ForeignKey(
        File, null=True, blank=True, on_delete=models.CASCADE, related_name="shares"
    )
    folder = models.ForeignKey(
        Folder, null=True, blank=True, on_delete=models.CASCADE, related_name="shares"
    )

    token = models.CharField(
        max_length=64, unique=True, default=generate_token, editable=False
    )

    permission_level = models.CharField(
        max_length=10, choices=LEVEL_CHOICES, default=READ
    )

    expires_at = models.DateTimeField(null=True, blank=True)
    password_hash = models.CharField(max_length=128, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(file__isnull=False, folder__isnull=True)
                    | models.Q(file__isnull=True, folder__isnull=False)
                ),
                name="share_exactly_one_target",
            )
        ]

    def set_password(self, raw_password):
        # 空字串代表「這個分享連結不設密碼」
        self.password_hash = make_password(raw_password) if raw_password else ""

    def check_password(self, raw_password):
        if not self.password_hash:
            return True
        return check_password(raw_password, self.password_hash)

    @property
    def is_expired(self):
        return self.expires_at is not None and timezone.now() >= self.expires_at

    def __str__(self):
        target = self.file or self.folder
        return f"share:{self.token[:8]}...-> {target}"