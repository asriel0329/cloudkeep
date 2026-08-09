from rest_framework import serializers

from app.files.models import File
from app.folders.models import Folder

from .models import Share


class ShareCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    file = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), required=False, allow_null=True
    )
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Share
        fields = [
            "id", "file", "folder", "permission_level",
            "expires_at", "password", "token", "created_at",
        ]
        read_only_fields = ["id", "token", "created_at"]

    def validate(self, attrs):
        file = attrs.get("file")
        folder = attrs.get("folder")

        if bool(file) == bool(folder):
            raise serializers.ValidationError(
                "必須指定 file 或 folder 其中一個，且只能指定一個。"
            )

        request = self.context["request"]
        target = file or folder
        if target.owner_id != request.user.id:
            raise serializers.ValidationError("你只能分享自己擁有的檔案或資料夾。")

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        share = Share(owner=self.context["request"].user, **validated_data)
        share.set_password(password)
        share.save()
        return share


class ShareSerializer(serializers.ModelSerializer):
    """列出自己建立過的分享連結時用，不會把密碼相關細節洩漏出去。"""

    has_password = serializers.SerializerMethodField()

    class Meta:
        model = Share
        fields = [
            "id", "file", "folder", "token",
            "permission_level", "expires_at", "has_password", "created_at",
        ]

    def get_has_password(self, obj):
        return bool(obj.password_hash)