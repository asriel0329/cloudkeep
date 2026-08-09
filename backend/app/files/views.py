import hashlib

from django.http import FileResponse, Http404
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from app.storage import get_storage

from .models import File
from .serializers import FileSerializer, FileUploadSerializer
from .utils import generate_storage_key


class FileListView(generics.ListAPIView):
    """
    GET /api/files/            -> 根目錄底下的檔案
    GET /api/files/?folder=5   -> id=5 資料夾底下的檔案
    """

    serializer_class = FileSerializer

    def get_queryset(self):
        queryset = File.objects.filter(owner=self.request.user)
        folder_id = self.request.query_params.get("folder")
        if folder_id is None:
            return queryset.filter(folder__isnull=True)
        return queryset.filter(folder_id=folder_id)


class FileUploadView(APIView):
    """
    POST /api/files/upload/   (multipart/form-data)
    fields: file, folder (可省略，代表存進根目錄)
    """

    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = FileUploadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        folder = serializer.validated_data.get("folder")

        # 邊讀邊算 SHA-256，避免一次把整個檔案塞進記憶體
        # （大檔案上傳時這件事很重要，不然容易把伺服器記憶體榨乾）
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        uploaded_file.seek(0)  # 算完 hash 要把讀取位置歸零，不然存檔會存到空的

        storage = get_storage()
        storage_key = generate_storage_key(request.user.id, uploaded_file.name)
        storage.save(uploaded_file, storage_key)

        file_obj = File.objects.create(
            name=uploaded_file.name,
            owner=request.user,
            folder=folder,
            storage_key=storage_key,
            hash=file_hash,
            size=uploaded_file.size,
            mime_type=uploaded_file.content_type or "application/octet-stream",
        )

        return Response(FileSerializer(file_obj).data, status=status.HTTP_201_CREATED)


class FileDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/files/<id>/  -> 檔案 metadata
    DELETE /api/files/<id>/  -> 刪除檔案（連同底層儲存的實際檔案一起刪）
    """

    serializer_class = FileSerializer

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        storage = get_storage()
        storage.delete(instance.storage_key)
        instance.delete()


class FileDownloadView(APIView):
    """GET /api/files/<id>/download/  -> 實際下載檔案內容"""

    def get(self, request, pk):
        try:
            file_obj = File.objects.get(pk=pk, owner=request.user)
        except File.DoesNotExist:
            raise Http404

        storage = get_storage()
        if not storage.exists(file_obj.storage_key):
            raise Http404

        file_handle = storage.open(file_obj.storage_key)
        response = FileResponse(
            file_handle, as_attachment=True, filename=file_obj.name
        )
        response["Content-Type"] = file_obj.mime_type
        return response