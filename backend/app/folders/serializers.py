from rest_framework import serializers

from .models import Folder


class FolderSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Folder
        fields = ["id", "name", "parent", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_parent(self, parent):
        if parent is None:
            return parent

        request = self.context.get("request")

        # 原本這裡只檢查「是不是你自己的資料夾」，現在改成檢查
        # 「你至少有唯讀權限」——因為現在資料夾可能是別人透過
        # Permission 授權給你的，不再只有擁有者才能操作。
        # 真正「能不能寫入」的權限會在 view 層另外檢查，這裡只做
        # 「這個資料夾對你來說存不存在」的基本檢查。
        from app.permissions.utils import has_read_access

        if not has_read_access(request.user, parent):
            raise serializers.ValidationError("找不到這個父資料夾。")

        return parent

    def validate_name(self, name):
        name = name.strip()
        if not name:
            raise serializers.ValidationError("資料夾名稱不能是空白。")
        if "/" in name or "\\" in name:
            raise serializers.ValidationError("資料夾名稱不能包含斜線。")
        return name
