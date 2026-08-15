from app.auditlog.utils import log_action

from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError

from app.permissions.utils import has_read_access, has_write_access

from .models import Folder
from .serializers import FolderSerializer

from django.utils import timezone
from .utils import cascade_restore, cascade_soft_delete

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app.auditlog.utils import log_action

class FolderListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/folders/            -> 列出自己根目錄下的資料夾
    GET  /api/folders/?parent=5   -> 列出 id=5 資料夾底下的子資料夾
                                      （只要對 id=5 有唯讀權限就能看，
                                      不限於自己擁有的資料夾）
    POST /api/folders/            -> 建立新資料夾（parent 底下要有寫入權限）
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        parent_id = self.request.query_params.get("parent")

        if parent_id is None:
            # 根目錄層級的列表沒有「被分享」的概念（Permission 是掛在
            # 具體某個資料夾上的），所以這裡維持只顯示自己擁有的。
            # 別人分享給你的資料夾，要透過 /api/permissions/shared-with-me/
            # 這支 API 另外查看。
            return Folder.objects.filter(owner=self.request.user, parent__isnull=True, is_deleted=False)

        parent = get_object_or_404(Folder, pk=parent_id)
        if not has_read_access(self.request.user, parent):
            raise PermissionDenied("你沒有權限查看這個資料夾。")

        return Folder.objects.filter(parent_id=parent_id, is_deleted=False)

    def perform_create(self, serializer):
        parent = serializer.validated_data.get("parent")

        if parent is not None and not has_write_access(self.request.user, parent):
            raise PermissionDenied("你沒有權限在這個資料夾底下建立子資料夾。")

        # 注意：owner 一律是「建立這個資料夾的人」，不是父資料夾的擁有者。
        # 例如 B 被 A 授權可寫入 A 的資料夾，B 在裡面建的子資料夾，
        # owner 是 B，但 parent 指向 A 的資料夾——這代表「這個子資料夾
        # 是 B 建立、放在 A 的空間裡」，跟 Nextcloud 的實際行為一致。
        serializer.save(owner=self.request.user)


class FolderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/folders/<id>/  -> 只要有唯讀權限就能看
    PATCH  /api/folders/<id>/  -> 需要寫入權限（改名/搬移）
    DELETE /api/folders/<id>/  -> 需要寫入權限
    """

    serializer_class = FolderSerializer

    def get_queryset(self):
        # 這裡刻意回傳「全部」資料夾，把權限判斷留給下面的方法，
        # 因為 GET 只需要 read，PATCH/DELETE 需要 write，
        # 兩種操作的門檻不一樣，不能用同一個 queryset 過濾解決。
        return Folder.objects.filter(is_deleted=False)

    def get_object(self):
        folder = super().get_object()
        if not has_read_access(self.request.user, folder):
            # 查不到就是查不到，回 404 而不是 403，
            # 避免洩漏「這個資料夾其實存在，只是你沒權限」這個資訊。
            from django.http import Http404

            raise Http404
        return folder

    def perform_update(self, serializer):
        folder = serializer.instance

        if not has_write_access(self.request.user, folder):
            raise PermissionDenied("你沒有權限修改這個資料夾。")

        parent = serializer.validated_data.get("parent", folder.parent)

        if parent is not None:
            if not has_write_access(self.request.user, parent):
                raise PermissionDenied("你沒有權限搬移到這個目標資料夾。")

            node = parent
            while node is not None:
                if node.id == folder.id:
                    raise ValidationError("不能把資料夾搬到自己的子資料夾底下。")
                node = node.parent

        serializer.save()

class FolderTrashListView(generics.ListAPIView):
    """GET /api/folders/trash/ —— 列出自己回收桶裡的資料夾"""

    serializer_class = FolderSerializer

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user, is_deleted=True)


class FolderRestoreView(APIView):
    """POST /api/folders/<id>/restore/"""

    def post(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, owner=request.user, is_deleted=True)
        cascade_restore(folder)
        log_action(request.user, "restore_folder", "folder", folder.id, folder.name)
        return Response(FolderSerializer(folder).data)


class FolderPermanentDeleteView(APIView):
    """DELETE /api/folders/<id>/permanent/ —— 從回收桶徹底刪除（連同底下所有內容）"""

    def delete(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, owner=request.user, is_deleted=True)

        from app.storage import get_storage

        storage = get_storage()

        def purge(f):
            for file_obj in f.files.all():
                storage.delete(file_obj.storage_key)
            for child in f.children.all():
                purge(child)

        purge(folder)
        log_action(request.user, "purge_folder", "folder", folder.id, folder.name)
        folder.delete()  # CASCADE 會一併刪掉底下所有子資料夾、檔案的資料庫記錄
        return Response(status=status.HTTP_204_NO_CONTENT)
