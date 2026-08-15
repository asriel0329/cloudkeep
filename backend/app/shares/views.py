from app.auditlog.utils import log_action

from django.http import FileResponse, Http404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.files.serializers import FileSerializer
from app.storage import get_storage

from .models import Share
from .serializers import ShareCreateSerializer, ShareSerializer


class ShareListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/shares/   -> 列出自己建立過的分享連結
    POST /api/shares/   -> 建立新的分享連結
         body: { "file": 1, "permission_level": "read",
                  "expires_at": "2026-12-31T00:00:00Z", "password": "" }
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return ShareCreateSerializer if self.request.method == "POST" else ShareSerializer

    def get_queryset(self):
        return Share.objects.filter(owner=self.request.user).order_by("-created_at")
    def perform_create(self, serializer):
        share = serializer.save()
        target = share.file or share.folder
        log_action(
            self.request.user,
            "create_share",
            "file" if share.file else "folder",
            target.id,
            target.name,
            detail=f"token={share.token[:8]}...",
        )
        
class ShareRevokeView(generics.DestroyAPIView):
    """DELETE /api/shares/<id>/ -> 撤銷分享連結（刪掉之後 token 立刻失效）"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Share.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        target = instance.file or instance.folder
        log_action(
            self.request.user,
            "revoke_share",
            "file" if instance.file else "folder",
            target.id if target else None,
            target.name if target else "",
            detail=f"token={instance.token[:8]}...",
        )
        instance.delete()


def _get_valid_share(token):
    try:
        share = Share.objects.get(token=token)
    except Share.DoesNotExist:
        raise Http404

    if share.is_expired:
        # 過期的連結直接視同不存在（回 404），不特別告訴對方
        # 「這個連結曾經存在過、只是過期了」，避免洩漏額外資訊。
        raise Http404

    return share


def _check_share_password(share, request):
    """回傳 None 代表密碼驗證通過（或本來就沒設密碼），否則回傳要直接回應的內容。"""
    if not share.password_hash:
        return None

    provided = request.query_params.get("password", "")
    if not share.check_password(provided):
        return Response(
            {"password_required": True}, status=status.HTTP_401_UNAUTHORIZED
        )

    return None


class SharePublicDetailView(APIView):
    """
    GET /api/shares/public/<token>/?password=xxx

    不需要登入。回傳分享目標的 metadata。
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        share = _get_valid_share(token)

        password_error = _check_share_password(share, request)
        if password_error:
            return password_error

        if share.file:
            return Response(
                {
                    "type": "file",
                    "permission_level": share.permission_level,
                    "file": FileSerializer(share.file).data,
                }
            )

        folder = share.folder
        return Response(
            {
                "type": "folder",
                "permission_level": share.permission_level,
                "folder": {"id": folder.id, "name": folder.name},
                "files": FileSerializer(folder.files.all(), many=True).data,
                "subfolders": [
                    {"id": f.id, "name": f.name} for f in folder.children.all()
                ],
            }
        )


class SharePublicDownloadView(APIView):
    """
    GET /api/shares/public/<token>/download/?password=xxx
        -> 分享的是檔案時，直接下載

    GET /api/shares/public/<token>/download/?password=xxx&file=5
        -> 分享的是資料夾時，用 ?file= 指定要下載該資料夾底下哪一個檔案
    """

    permission_classes = [AllowAny]

    def get(self, request, token):
        share = _get_valid_share(token)

        password_error = _check_share_password(share, request)
        if password_error:
            return password_error

        if share.file:
            file_obj = share.file
        else:
            file_id = request.query_params.get("file")
            if not file_id:
                return Response(
                    {"detail": "這是資料夾分享，請帶上 ?file=<檔案id> 指定要下載哪一個檔案。"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            file_obj = share.folder.files.filter(pk=file_id).first()
            if file_obj is None:
                raise Http404

        storage = get_storage()
        if not storage.exists(file_obj.storage_key):
            raise Http404

        log_action(
            None,  # 透過分享連結存取的人不用登入，沒有對應的使用者帳號
            "download_via_share",
            "file",
            file_obj.id,
            file_obj.name,
            detail=f"token={share.token[:8]}...",
        )
        
        file_handle = storage.open(file_obj.storage_key)
        response = FileResponse(
            file_handle, as_attachment=True, filename=file_obj.name
        )
        response["Content-Type"] = file_obj.mime_type
        return response