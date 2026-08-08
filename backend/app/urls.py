"""
專案總路由。

各模組的 urls.py 完成後，依序在這裡用 include() 掛進來，例如：
    path("api/auth/", include("app.auth.urls")),
    path("api/folders/", include("app.folders.urls")),
    path("api/files/", include("app.files.urls")),
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """簡單的健康檢查端點，確認 Django + DB 連線是否正常。"""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    # 批次 1 之後陸續打開：
    # path("api/auth/", include("app.auth.urls")),
    # path("api/folders/", include("app.folders.urls")),
    # path("api/files/", include("app.files.urls")),
    # path("api/shares/", include("app.shares.urls")),
]
