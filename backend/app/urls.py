"""
專案總路由。

各模組的 urls.py 完成後，依序在這裡用 include() 掛進來。
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """簡單的健康檢查端點，確認 Django + DB 連線是否正常。"""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/auth/", include("app.auth.urls")),
    path("api/folders/", include("app.folders.urls")),
    # 之後的批次陸續打開：
    path("api/files/", include("app.files.urls")),
    # path("api/shares/", include("app.shares.urls")),
]
