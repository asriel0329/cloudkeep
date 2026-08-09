from rest_framework import serializers

from app.folders.models import Folder

from .models import File


class FileSerializer(serializers.ModelSerializer):
    """列出/查看檔案 metadata 用，全部欄位唯讀——真正的上傳走另一支 API。"""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = File
        fields = [
            "id", "name", "folder", "owner",
            "size", "mime_type", "hash", "created_at", "updated_at",
        ]
        read_only_fields = fields


class FileUploadSerializer(serializers.Serializer):
    """
    上傳用的 serializer 不對應到 model 的所有欄位，因為 storage_key、
    hash、size、mime_type 這些欄位不是「使用者填的」，是後端根據
    上傳的檔案內容自動算出來的。
    """

    file = serializers.FileField()
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), required=False, allow_null=True
    )

    def validate_folder(self, folder):
        if folder is None:
            return folder

        request = self.context["request"]

        # 原本只檢查擁有者，現在改成檢查是否有寫入權限
        # （因為要能「上傳檔案到這個資料夾」，至少要有 write）
        from app.permissions.utils import has_write_access

        if not has_write_access(request.user, folder):
            raise serializers.ValidationError("找不到這個資料夾，或你沒有寫入權限。")

        return folder