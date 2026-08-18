import hashlib

from django.db import IntegrityError, transaction
from django.db.models import Max
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

from .models import Blob, File, FileVersion, UploadSession
from .quota import get_used_bytes, has_quota_for
from .serializers import FileSerializer, FileUploadSerializer, FileVersionSerializer
from .tasks import process_uploaded_blob
from .upload_session import assemble, cleanup, create_session, is_complete, save_chunk
from .utils import generate_storage_key, release_blob_reference


class QuotaExceeded(Exception):
    pass

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


def _get_or_create_blob(content_stream, file_hash, size, filename):
    with transaction.atomic():
        existing = Blob.objects.select_for_update().filter(hash=file_hash).first()
        if existing:
            existing.reference_count = existing.reference_count + 1
            existing.save(update_fields=["reference_count"])
            return existing, False

    storage = get_storage()
    storage_key = generate_storage_key(0, filename)
    storage.save(content_stream, storage_key)

    try:
        blob = Blob.objects.create(
            hash=file_hash, storage_key=storage_key, size=size, reference_count=1
        )
        return blob, True
    except IntegrityError:
        storage.delete(storage_key)
        blob = Blob.objects.get(hash=file_hash)
        blob.reference_count = blob.reference_count + 1
        blob.save(update_fields=["reference_count"])
        return blob, False

def _finalize_file(user, folder, name, mime_type, size, content_stream, file_hash):
    """
    不管是一般上傳還是分塊上傳組裝完成，最後都走這個函式：
    去重（是否已有同 hash 的 Blob）+ 是否覆蓋既有同名檔案（版本控制）。
    """

    if not has_quota_for(user, size):
        raise QuotaExceeded()

    blob, _ = _get_or_create_blob(content_stream, file_hash, size, name)

    existing_file = File.objects.filter(
        owner=user, folder=folder, name=name, is_deleted=False
    ).first()

    if existing_file:
        if existing_file.folder is None:
            allowed = existing_file.owner_id == user.id
        else:
            allowed = has_write_access(user, existing_file.folder)

        if not allowed:
            raise PermissionDenied("你沒有權限覆蓋這個檔案。")

        next_version = (
            existing_file.versions.aggregate(m=Max("version_number"))["m"] or 0
        ) + 1

        FileVersion.objects.create(
            file=existing_file, blob=blob, version_number=next_version, created_by=user
        )

        existing_file.blob = blob
        existing_file.mime_type = mime_type
        existing_file.save(update_fields=["blob", "mime_type", "updated_at"])

        transaction.on_commit(lambda: process_uploaded_blob.delay(blob.id))
        log_action(user, "new_version", "file", existing_file.id, existing_file.name, detail=f"v{next_version}")

        return existing_file, False

    file_obj = File.objects.create(name=name, owner=user, folder=folder, blob=blob, mime_type=mime_type)
    FileVersion.objects.create(file=file_obj, blob=blob, version_number=1, created_by=user)

    transaction.on_commit(lambda: process_uploaded_blob.delay(blob.id))
    log_action(user, "upload", "file", file_obj.id, file_obj.name)

    return file_obj, True

class FileUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        folder = serializer.validated_data.get("folder")

        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        uploaded_file.seek(0)

        try:
            file_obj, created = _finalize_file(
                request.user,
                folder,
                uploaded_file.name,
                uploaded_file.content_type or "application/octet-stream",
                uploaded_file.size,
                uploaded_file,
                file_hash,
            )
        except QuotaExceeded:
            return Response(
                {"detail": "儲存空間不足，請刪除一些檔案或聯繫管理員提高配額。"},
                status=status.HTTP_507_INSUFFICIENT_STORAGE,
            )

        return Response(
            FileSerializer(file_obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

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

        # 這個檔案曾經有過的每一個版本，各自佔用一個 Blob 的引用，
        # 全部都要釋放掉，不然舊版本的內容會變成永遠回收不了的孤兒。
        blob_ids = list(file_obj.versions.values_list("blob_id", flat=True))
        file_obj.delete()  # CASCADE 會一併刪掉底下所有 FileVersion 記錄

        for blob_id in blob_ids:
            release_blob_reference(blob_id)

        return Response(status=status.HTTP_204_NO_CONTENT)

class FileVersionListView(generics.ListAPIView):
    """GET /api/files/<id>/versions/"""

    serializer_class = FileVersionSerializer

    def get_queryset(self):
        file_obj = get_object_or_404(File, pk=self.kwargs["pk"], is_deleted=False)

        if file_obj.folder is None:
            allowed = file_obj.owner_id == self.request.user.id
        else:
            allowed = has_read_access(self.request.user, file_obj.folder)

        if not allowed:
            raise Http404

        return file_obj.versions.all()

class FileVersionRestoreView(APIView):
    """POST /api/files/<id>/versions/<version_number>/restore/"""

    def post(self, request, pk, version_number):
        file_obj = get_object_or_404(File, pk=pk, is_deleted=False)

        if file_obj.folder is None:
            allowed = file_obj.owner_id == request.user.id
        else:
            allowed = has_write_access(request.user, file_obj.folder)

        if not allowed:
            raise PermissionDenied("你沒有權限還原這個檔案的版本。")

        version = get_object_or_404(FileVersion, file=file_obj, version_number=version_number)

        file_obj.blob = version.blob
        file_obj.save(update_fields=["blob", "updated_at"])

        log_action(
            request.user, "restore_version", "file", file_obj.id, file_obj.name,
            detail=f"v{version_number}",
        )

        return Response(FileSerializer(file_obj).data)

class FileVersionDownloadView(APIView):
    """GET /api/files/<id>/versions/<version_number>/download/"""

    def get(self, request, pk, version_number):
        file_obj = get_object_or_404(File, pk=pk, is_deleted=False)

        if file_obj.folder is None:
            allowed = file_obj.owner_id == request.user.id
        else:
            allowed = has_read_access(request.user, file_obj.folder)

        if not allowed:
            raise Http404

        version = get_object_or_404(FileVersion, file=file_obj, version_number=version_number)

        storage = get_storage()
        if not storage.exists(version.blob.storage_key):
            raise Http404

        log_action(
            request.user, "download_version", "file", file_obj.id, file_obj.name,
            detail=f"v{version_number}",
        )

        file_handle = storage.open(version.blob.storage_key)
        response = FileResponse(
            file_handle, as_attachment=True, filename=f"v{version_number}_{file_obj.name}"
        )
        response["Content-Type"] = file_obj.mime_type
        return response

class UploadSessionInitView(APIView):
    """
    POST /api/files/upload/sessions/
    body: { "filename": "...", "size": 12345678, "mime_type": "...", "folder": <id 或不傳> }
    回傳 session id、每塊大小、總共要切幾塊，前端依此切檔案分批上傳。
    """

    def post(self, request):
        filename = request.data.get("filename")
        size = request.data.get("size")
        mime_type = request.data.get("mime_type", "application/octet-stream")
        folder_id = request.data.get("folder")

        if not filename or not size:
            return Response({"detail": "filename 與 size 為必填"}, status=status.HTTP_400_BAD_REQUEST)

        size = int(size)

        folder = None
        if folder_id:
            folder = get_object_or_404(Folder, pk=folder_id)
            if not has_write_access(request.user, folder):
                raise PermissionDenied("你沒有權限上傳到這個資料夾。")

        if not has_quota_for(request.user, size):
            return Response(
                {"detail": "儲存空間不足，請刪除一些檔案或聯繫管理員提高配額。"},
                status=status.HTTP_507_INSUFFICIENT_STORAGE,
            )

        session = create_session(request.user, folder, filename, mime_type, size)

        return Response(
            {
                "id": str(session.id),
                "chunk_size": session.chunk_size,
                "total_chunks": session.total_chunks,
                "received_chunks": session.received_chunks,
            },
            status=status.HTTP_201_CREATED,
        )


class UploadChunkView(APIView):
    """
    PUT /api/files/upload/sessions/<session_id>/chunks/<chunk_number>/
    body (multipart/form-data): chunk=<這一塊的二進位內容>
    """

    parser_classes = [MultiPartParser]

    def put(self, request, session_id, chunk_number):
        session = get_object_or_404(UploadSession, pk=session_id, owner=request.user)

        if session.status != UploadSession.STATUS_UPLOADING:
            return Response({"detail": "這個上傳工作階段已經結束或失效"}, status=status.HTTP_400_BAD_REQUEST)

        if chunk_number < 0 or chunk_number >= session.total_chunks:
            return Response({"detail": "chunk_number 超出範圍"}, status=status.HTTP_400_BAD_REQUEST)

        chunk_file = request.data.get("chunk")
        if chunk_file is None:
            return Response({"detail": "缺少 chunk 欄位"}, status=status.HTTP_400_BAD_REQUEST)

        save_chunk(session, chunk_number, chunk_file)
        session.refresh_from_db()

        return Response({"received_chunks": session.received_chunks, "is_complete": is_complete(session)})


class UploadSessionStatusView(APIView):
    """
    GET /api/files/upload/sessions/<session_id>/
    斷線重連後，前端查這支 API 知道「已經收到哪些分塊」，
    只補傳缺的部分即可，這就是 resumable upload 的核心。
    """

    def get(self, request, session_id):
        session = get_object_or_404(UploadSession, pk=session_id, owner=request.user)
        return Response(
            {
                "id": str(session.id),
                "filename": session.filename,
                "status": session.status,
                "chunk_size": session.chunk_size,
                "total_chunks": session.total_chunks,
                "received_chunks": session.received_chunks,
            }
        )


class UploadCompleteView(APIView):
    """
    POST /api/files/upload/sessions/<session_id>/complete/
    所有分塊都上傳完後呼叫，伺服器把分塊組回完整檔案，
    走跟一般上傳完全一樣的 hash / 去重 / 版本控制邏輯。
    """

    def post(self, request, session_id):
        session = get_object_or_404(UploadSession, pk=session_id, owner=request.user)

        if not is_complete(session):
            missing = [i for i in range(session.total_chunks) if i not in session.received_chunks]
            return Response(
                {"detail": "還有分塊沒收到", "missing_chunks": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.status = UploadSession.STATUS_ASSEMBLING
        session.save(update_fields=["status", "updated_at"])

        assembled_path = assemble(session)

        hasher = hashlib.sha256()
        with open(assembled_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        file_hash = hasher.hexdigest()

        try:
            with open(assembled_path, "rb") as content_stream:
                file_obj, created = _finalize_file(
                    request.user,
                    session.folder,
                    session.filename,
                    session.mime_type,
                    session.total_size,
                    content_stream,
                    file_hash,
                )
        except QuotaExceeded:
            session.status = UploadSession.STATUS_FAILED
            session.save(update_fields=["status", "updated_at"])
            cleanup(session)
            return Response(
                {"detail": "儲存空間不足，請刪除一些檔案或聯繫管理員提高配額。"},
                status=status.HTTP_507_INSUFFICIENT_STORAGE,
            )

        session.status = UploadSession.STATUS_COMPLETED
        session.save(update_fields=["status", "updated_at"])
        cleanup(session)

        return Response(
            FileSerializer(file_obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

