import hashlib
from app.auditlog.utils import log_action

from django.http import FileResponse, Http404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .quota import has_quota_for
from .quota import get_used_bytes

from .tasks import process_uploaded_file
from app.permissions.utils import has_read_access, has_write_access
from app.storage import get_storage

from .models import File
from .serializers import FileSerializer, FileUploadSerializer
from .utils import generate_storage_key


class FileListView(generics.ListAPIView):
    """
    GET /api/files/            -> 根目錄底下自己的檔案
    GET /api/files/?folder=5   -> id=5 資料夾底下的檔案（有唯讀權限就能看）
    """

    serializer_class = FileSerializer

    def get_queryset(self):
        folder_id = self.request.query_params.get("folder")

        if folder_id is None:
            return File.objects.filter(owner=self.request.user, folder__isnull=True)

        from django.shortcuts import get_object_or_404

        from app.folders.models import Folder

        folder = get_object_or_404(Folder, pk=folder_id)
        if not has_read_access(self.request.user, folder):
            raise PermissionDenied("你沒有權限查看這個資料夾。")

        return File.objects.filter(folder_id=folder_id)


class FileUploadView(APIView):
    """
    POST /api/files/upload/   (multipart/form-data)
    fields: file, folder (可省略，代表存進自己的根目錄)
    """

    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = FileUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        folder = serializer.validated_data.get("folder")

        if not has_quota_for(request.user, uploaded_file.size):
            return Response(
                {"detail": "儲存空間不足，請刪除一些檔案或聯繫管理員提高配額。"},
                status=status.HTTP_507_INSUFFICIENT_STORAGE,
            )

        storage = get_storage()
        storage_key = generate_storage_key(request.user.id, uploaded_file.name)
        storage.save(uploaded_file, storage_key)

        # 注意：檔案的 owner 是「上傳的人」，不是資料夾擁有者，邏輯跟
        # Folder 的 perform_create 一致——你上傳到別人分享給你、且你
        # 有寫入權限的資料夾裡，這個檔案仍然是「你上傳的」。
        file_obj = File.objects.create(
            name=uploaded_file.name,
            owner=request.user,
            folder=folder,
            storage_key=storage_key,
            size=uploaded_file.size,
            mime_type=uploaded_file.content_type or "application/octet-stream",
        )
        # 用 on_commit 確保這筆 File 記錄真的寫進資料庫、交易確定成功後，
        # 才通知 Celery 去處理——避免 race condition：worker 搶快了，
        # 這邊的 transaction 卻還沒 commit，worker 查不到這筆記錄。
        transaction.on_commit(lambda: process_uploaded_file.delay(file_obj.id))

        log_action(request.user, "upload", "file", file_obj.id, file_obj.name)

        return Response(FileSerializer(file_obj).data, status=status.HTTP_201_CREATED)


class FileDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/files/<id>/  -> 有唯讀權限就能看
    DELETE /api/files/<id>/  -> 需要寫入權限
    """

    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.all()

    def get_object(self):
        file_obj = super().get_object()

        # 根目錄底下的檔案（folder=None）沒有 Permission 概念可以繼承，
        # 這時候只能靠「是不是擁有者」判斷；有 folder 的話，
        # 就看對那個 folder 的權限。
        if file_obj.folder is None:
            allowed = file_obj.owner_id == self.request.user.id
        else:
            allowed = has_read_access(self.request.user, file_obj.folder)

        if not allowed:
            raise Http404

        return file_obj

    def perform_destroy(self, instance):
        if instance.folder is None:
            allowed = instance.owner_id == self.request.user.id
        else:
            allowed = has_write_access(self.request.user, instance.folder)

        if not allowed:
            raise PermissionDenied("你沒有權限刪除這個檔案。")

        log_action(self.request.user, "delete_file", "file", instance.id, instance.name)
        storage = get_storage()
        storage.delete(instance.storage_key)
        instance.delete()


class FileDownloadView(APIView):
    """GET /api/files/<id>/download/"""

    def get(self, request, pk):
        try:
            file_obj = File.objects.get(pk=pk)
        except File.DoesNotExist:
            raise Http404

        if file_obj.folder is None:
            allowed = file_obj.owner_id == request.user.id
        else:
            allowed = has_read_access(request.user, file_obj.folder)

        if not allowed:
            raise Http404

        storage = get_storage()
        if not storage.exists(file_obj.storage_key):
            raise Http404

        log_action(request.user, "download", "file", file_obj.id, file_obj.name)
        file_handle = storage.open(file_obj.storage_key)
        response = FileResponse(
            file_handle, as_attachment=True, filename=file_obj.name
        )
        response["Content-Type"] = file_obj.mime_type
        return response

class FileThumbnailView(APIView):
    """GET /api/files/<id>/thumbnail/"""

    def get(self, request, pk):
        try:
            file_obj = File.objects.get(pk=pk)
        except File.DoesNotExist:
            raise Http404

        if not file_obj.thumbnail_key:
            raise Http404

        if file_obj.folder is None:
            allowed = file_obj.owner_id == request.user.id
        else:
            allowed = has_read_access(request.user, file_obj.folder)

        if not allowed:
            raise Http404

        storage = get_storage()
        if not storage.exists(file_obj.thumbnail_key):
            raise Http404

        file_handle = storage.open(file_obj.thumbnail_key)
        return FileResponse(file_handle, content_type="image/png")

class StorageQuotaView(APIView):
    """GET /api/files/quota/ —— 回傳目前使用者的儲存空間使用狀況"""

    def get(self, request):
        used = get_used_bytes(request.user)
        return Response(
            {
                "used_bytes": used,
                "quota_bytes": request.user.storage_quota_bytes,
                "percentage": round(used / request.user.storage_quota_bytes * 100, 1)
                if request.user.storage_quota_bytes
                else 0,
            }
        )