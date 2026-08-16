import hashlib

from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from app.auditlog.utils import log_action
from app.folders.models import Folder
from app.permissions.utils import has_read_access, has_write_access
from app.storage import get_storage

from .models import Blob, File
from .quota import get_used_bytes, has_quota_for
from .serializers import FileSerializer, FileUploadSerializer
from .tasks import process_uploaded_blob
from .utils import generate_storage_key, release_blob_reference


class FileListView(generics.ListAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):
        folder_id = self.request.query_params.get("folder")

        if folder_id is None:
            return File.objects.filter(owner=self.request.user, folder__isnull=True, is_deleted=False)

        folder = get_object_or_404(Folder, pk=folder_id)
        if not has_read_access(self.request.user, folder):
            raise PermissionDenied("你沒有權限查看這個資料夾。")

        return File.objects.filter(folder_id=folder_id, is_deleted=False)


def _get_or_create_blob(uploaded_file, file_hash):
    """
    去重偵測的核心：這份 hash 之前有沒有出現過？
    有 -> 直接複用既有 Blob，不用真的再存一次進 Storage。
    沒有 -> 真的把內容存進 Storage，建立新的 Blob。
    """

    with transaction.atomic():
        existing = Blob.objects.select_for_update().filter(hash=file_hash).first()
        if existing:
            existing.reference_count = existing.reference_count + 1
            existing.save(update_fields=["reference_count"])
            return existing, False

    # 這裡故意離開上面的 transaction 才寫 Storage：檔案 I/O 不該卡在
    # 資料庫交易裡面，避免長時間鎖住資料表。
    storage = get_storage()
    storage_key = generate_storage_key(0, uploaded_file.name)  # owner id 不再需要綁在路徑上，Blob 是全域共用的
    uploaded_file.seek(0)
    storage.save(uploaded_file, storage_key)

    try:
        blob = Blob.objects.create(
            hash=file_hash,
            storage_key=storage_key,
            size=uploaded_file.size,
            reference_count=1,
        )
        return blob, True
    except IntegrityError:
        # 極少數情況：兩個請求幾乎同時上傳同一份新內容，都判斷「不存在」，
        # 都跑到這裡才發現對方先建立好了。把自己剛寫的那份多餘檔案清掉，
        # 改用對方建立的 Blob。
        storage.delete(storage_key)
        blob = Blob.objects.get(hash=file_hash)
        blob.reference_count = blob.reference_count + 1
        blob.save(update_fields=["reference_count"])
        return blob, False


class FileUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        folder = serializer.validated_data.get("folder")

        if not has_quota_for(request.user, uploaded_file.size):
            return Response(
                {"detail": "儲存空間不足，請刪除一些檔案或聯繫管理員提高配額。"},
                status=status.HTTP_507_INSUFFICIENT_STORAGE,
            )

        # 先算 hash，這一步一定要在決定「要不要真的寫進 Storage」之前完成。
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        uploaded_file.seek(0)

        blob, is_new_blob = _get_or_create_blob(uploaded_file, file_hash)

        file_obj = File.objects.create(
            name=uploaded_file.name,
            owner=request.user,
            folder=folder,
            blob=blob,
            mime_type=uploaded_file.content_type or "application/octet-stream",
        )

        # 即使 Blob 不是新的，也觸發任務——task 內部會自己檢查
        # processing_status 是不是已經 DONE，是的話會直接跳過，
        # 不會重複產生縮圖。
        transaction.on_commit(lambda: process_uploaded_blob.delay(blob.id))

        log_action(request.user, "upload", "file", file_obj.id, file_obj.name)

        return Response(FileSerializer(file_obj).data, status=status.HTTP_201_CREATED)


class FileDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(is_deleted=False)

    def get_object(self):
        file_obj = super().get_object()

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

        log_action(self.request.user, "trash_file", "file", instance.id, instance.name)

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_deleted", "deleted_at"])


class FileDownloadView(APIView):
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
        if not storage.exists(file_obj.blob.storage_key):
            raise Http404

        log_action(request.user, "download", "file", file_obj.id, file_obj.name)
        file_handle = storage.open(file_obj.blob.storage_key)
        response = FileResponse(file_handle, as_attachment=True, filename=file_obj.name)
        response["Content-Type"] = file_obj.mime_type
        return response


class FileThumbnailView(APIView):
    def get(self, request, pk):
        try:
            file_obj = File.objects.get(pk=pk)
        except File.DoesNotExist:
            raise Http404

        if not file_obj.blob.thumbnail_key:
            raise Http404

        if file_obj.folder is None:
            allowed = file_obj.owner_id == request.user.id
        else:
            allowed = has_read_access(request.user, file_obj.folder)

        if not allowed:
            raise Http404

        storage = get_storage()
        if not storage.exists(file_obj.blob.thumbnail_key):
            raise Http404

        file_handle = storage.open(file_obj.blob.thumbnail_key)
        return FileResponse(file_handle, content_type="image/png")


class StorageQuotaView(APIView):
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


class FileTrashListView(generics.ListAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user, is_deleted=True)


class FileRestoreView(APIView):
    def post(self, request, pk):
        file_obj = get_object_or_404(File, pk=pk, owner=request.user, is_deleted=True)
        file_obj.is_deleted = False
        file_obj.deleted_at = None
        file_obj.save(update_fields=["is_deleted", "deleted_at"])
        log_action(request.user, "restore_file", "file", file_obj.id, file_obj.name)
        return Response(FileSerializer(file_obj).data)


class FilePermanentDeleteView(APIView):
    def delete(self, request, pk):
        file_obj = get_object_or_404(File, pk=pk, owner=request.user, is_deleted=True)

        log_action(request.user, "purge_file", "file", file_obj.id, file_obj.name)

        blob_id = file_obj.blob_id
        file_obj.delete()
        release_blob_reference(blob_id)

        return Response(status=status.HTTP_204_NO_CONTENT)