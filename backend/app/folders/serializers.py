from rest_framework import serializers

from .models import Folder


class FolderSerializer(serializers.ModelSerializer):
    """
    owner 設成 read_only：使用者不能透過 API 假造「這個資料夾是別人的」，
    owner 一律由後端在 view 裡自動填成「目前登入的使用者」（request.user），
    這是很基本但重要的安全習慣——凡是「歸屬權」相關的欄位，都不該讓
    前端自己填，一定要後端從登入狀態決定。
    """

    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    # 明確宣告 parent 欄位、明講它不是必填，不要依賴 DRF 自動根據
    # model 的 null/blank 去推斷「必填與否」。不同版本的 DRF 對這個
    # 推斷邏輯不完全一致，明確寫出來比較保險：不帶 parent 或傳
    # null，都代表「這是根目錄底下的資料夾」。
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

        # 防止使用者把資料夾的 parent 指向「別人的資料夾」，
        # 不然 A 使用者理論上可以偷偷把自己的資料夾塞進 B 使用者的樹裡。
        if parent.owner_id != request.user.id:
            raise serializers.ValidationError("找不到這個父資料夾。")

        return parent

    def validate_name(self, name):
        name = name.strip()
        if not name:
            raise serializers.ValidationError("資料夾名稱不能是空白。")
        if "/" in name or "\\" in name:
            raise serializers.ValidationError("資料夾名稱不能包含斜線。")
        return name
