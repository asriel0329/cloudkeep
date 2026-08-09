from django.urls import path

from .views import (
    SharePublicDetailView,
    SharePublicDownloadView,
    ShareListCreateView,
    ShareRevokeView,
)

urlpatterns = [
    path("", ShareListCreateView.as_view(), name="share-list-create"),
    path("<int:pk>/", ShareRevokeView.as_view(), name="share-revoke"),
    path("public/<str:token>/", SharePublicDetailView.as_view(), name="share-public-detail"),
    path(
        "public/<str:token>/download/",
        SharePublicDownloadView.as_view(),
        name="share-public-download",
    ),
]