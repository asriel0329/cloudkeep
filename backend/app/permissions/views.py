from rest_framework import generics

from app.folders.models import Folder

from .models import Permission
from .serializers import PermissionSerializer


class PermissionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/permissions/?folder=5   -> 列出 id=5 資料夾的授權名單
    POST /api/permissions/            -> 新增授權
         body: { "folder": 5, "user": 3, "level": "read" }
    """

    serializer_class = PermissionSerializer

    def get_queryset(self):
        # 只能看到「自己擁有的資料夾」上的授權名單，
        # 不能偷看別人資料夾分享給了誰。
        queryset = Permission.objects.filter(folder__owner=self.request.user)
        folder_id = self.request.query_params.get("folder")
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        return queryset


class PermissionRevokeView(generics.DestroyAPIView):
    """DELETE /api/permissions/<id>/ -> 撤銷授權"""

    serializer_class = PermissionSerializer

    def get_queryset(self):
        return Permission.objects.filter(folder__owner=self.request.user)


class SharedWithMeView(generics.ListAPIView):
    """
    GET /api/permissions/shared-with-me/
    列出「別人直接授權給我」的資料夾（注意：這裡只列出直接被授權的，
    不會列出因為繼承而有權限、但沒被直接授權的更深層子資料夾，
    這是刻意的簡化，避免列表查詢要遞迴整棵樹）
    """

    from app.folders.serializers import FolderSerializer

    serializer_class = FolderSerializer

    def get_queryset(self):
        folder_ids = Permission.objects.filter(
            user=self.request.user
        ).values_list("folder_id", flat=True)
        return Folder.objects.filter(id__in=folder_ids)