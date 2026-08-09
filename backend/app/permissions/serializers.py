from rest_framework import serializers

from app.folders.models import Folder

from .models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    folder = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all())

    class Meta:
        model = Permission
        fields = ["id", "folder", "user", "level", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_folder(self, folder):
        request = self.context["request"]
        # 只有資料夾的擁有者才能授權給別人，不然任何人都能幫別人的
        # 資料夾發權限，這是明顯的資安漏洞。
        if folder.owner_id != request.user.id:
            raise serializers.ValidationError("你不是這個資料夾的擁有者。")
        return folder