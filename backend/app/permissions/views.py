from rest_framework import generics
from rest_framework.response import Response

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
    列出別人直接授權給我的資料夾，
    並附上我對該資料夾的權限等級。
    """

    def get(self, request, *args, **kwargs):
        permissions = Permission.objects.filter(
            user=request.user
        ).select_related("folder")

        data = [
            {
                "id": permission.folder.id,
                "name": permission.folder.name,
                "parent": permission.folder.parent_id,
                "owner": permission.folder.owner.username,
                "permission_level": permission.level,
                "created_at": permission.folder.created_at,
                "updated_at": permission.folder.updated_at,
            }
            for permission in permissions
        ]

        return Response(data)