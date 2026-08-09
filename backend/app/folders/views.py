from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Folder
from .serializers import FolderSerializer


class FolderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/folders/            -> 列出目前使用者根目錄下的資料夾
    GET  /api/folders/?parent=5   -> 列出 id=5 這個資料夾底下的子資料夾
    POST /api/folders/            -> 建立新資料夾
         body: { "name": "...", "parent": null 或 父資料夾 id }
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        # 只能看到自己的資料夾，看不到別人的（這行是權限的核心）
        queryset = Folder.objects.filter(owner=self.request.user)

        parent_id = self.request.query_params.get("parent")
        if parent_id is None:
            # 沒帶 parent 參數 -> 回傳根目錄底下的資料夾
            return queryset.filter(parent__isnull=True)

        return queryset.filter(parent_id=parent_id)

    def perform_create(self, serializer):
        # owner 一律是目前登入的使用者，不接受前端傳入
        serializer.save(owner=self.request.user)


class FolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/folders/<id>/  -> 取得單一資料夾資訊
    PATCH  /api/folders/<id>/  -> 重新命名（也可以順便改 parent 來搬移資料夾）
    DELETE /api/folders/<id>/  -> 刪除資料夾（底下的子資料夾會一併被刪除，
                                   因為 model 裡 parent 設了 on_delete=CASCADE）
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        # 同樣限制只能操作自己的資料夾，
        # 就算有人猜到別人的資料夾 id，這裡查詢直接查不到，回 404。
        return Folder.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        parent = serializer.validated_data.get("parent", serializer.instance.parent)
        folder = serializer.instance

        # 防止把資料夾搬到自己底下（會造成循環，樹狀結構壞掉）
        if parent is not None:
            node = parent
            while node is not None:
                if node.id == folder.id:
                    raise ValidationError("不能把資料夾搬到自己的子資料夾底下。")
                node = node.parent

        serializer.save()
