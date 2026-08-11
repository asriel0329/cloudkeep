from rest_framework import serializers

from app.folders.models import Folder

from .models import File


class FileSerializer(serializers.ModelSerializer):
    """列出/查看檔案 metadata 用，全部欄位唯讀。"""

    owner = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "name",
            "folder",
            "owner",
            "size",
            "mime_type",
            "hash",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_owner(self, obj):
        return {
            "id": obj.owner.id,
            "username": obj.owner.username,
        }


class FileUploadSerializer(serializers.Serializer):
    """
    上傳用的 serializer 不對應到 model 的所有欄位。
    storage_key、hash、size、mime_type 等欄位由後端自動產生。
    """

    file = serializers.FileField()

    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False,
        allow_null=True,
    )

    def validate_folder(self, folder):
        if folder is None:
            return folder

        request = self.context["request"]

        from app.permissions.utils import has_write_access

        if not has_write_access(request.user, folder):
            raise serializers.ValidationError(
                "找不到這個資料夾，或你沒有寫入權限。"
            )

        return folder