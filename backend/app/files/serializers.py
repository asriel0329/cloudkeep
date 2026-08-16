from rest_framework import serializers

from app.folders.models import Folder

from .models import File


class FileSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    has_thumbnail = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    hash = serializers.SerializerMethodField()
    processing_status = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id", "name", "folder", "owner", "size", "mime_type",
            "hash", "processing_status", "has_thumbnail",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_has_thumbnail(self, obj):
        return bool(obj.blob.thumbnail_key)

    def get_size(self, obj):
        return obj.blob.size

    def get_hash(self, obj):
        return obj.blob.hash

    def get_processing_status(self, obj):
        return obj.blob.processing_status

    def get_owner(self, obj):
        return {"id": obj.owner.id, "username": obj.owner.username}


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