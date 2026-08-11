from rest_framework import serializers
from django.contrib.auth import get_user_model

from app.folders.models import Folder

from .models import Permission


User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all()
    )

    user = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field="username",
    )

    class Meta:
        model = Permission
        fields = ["id", "folder", "user", "level", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_folder(self, folder):
        request = self.context["request"]

        # 只有資料夾的擁有者才能授權給別人
        if folder.owner_id != request.user.id:
            raise serializers.ValidationError(
                "你不是這個資料夾的擁有者。"
            )

        return folder