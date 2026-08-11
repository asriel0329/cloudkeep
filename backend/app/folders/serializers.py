from rest_framework import serializers

from .models import Folder


class FolderSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Folder
        fields = [
            "id",
            "name",
            "parent",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_owner(self, obj):
        return {
            "id": obj.owner.id,
            "username": obj.owner.username,
        }

    def validate_parent(self, parent):
        if parent is None:
            return parent

        request = self.context.get("request")

        from app.permissions.utils import has_read_access

        if not has_read_access(request.user, parent):
            raise serializers.ValidationError("找不到這個父資料夾。")

        return parent

    def validate_name(self, name):
        name = name.strip()

        if not name:
            raise serializers.ValidationError("資料夾名稱不能是空白。")

        if "/" in name or "\\" in name:
            raise serializers.ValidationError(
                "資料夾名稱不能包含斜線。"
            )

        return name