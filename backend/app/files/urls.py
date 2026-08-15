from django.urls import path

from .views import (
    FileDetailView,
    FileDownloadView,
    FileListView,
    FilePermanentDeleteView,
    FileRestoreView,
    FileThumbnailView,
    FileTrashListView,
    FileUploadView,
    StorageQuotaView,
)

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("quota/", StorageQuotaView.as_view(), name="file-quota"),
    path("trash/", FileTrashListView.as_view(), name="file-trash-list"),
    path("<int:pk>/", FileDetailView.as_view(), name="file-detail"),
    path("<int:pk>/download/", FileDownloadView.as_view(), name="file-download"),
    path("<int:pk>/thumbnail/", FileThumbnailView.as_view(), name="file-thumbnail"),
    path("<int:pk>/restore/", FileRestoreView.as_view(), name="file-restore"),
    path("<int:pk>/permanent/", FilePermanentDeleteView.as_view(), name="file-permanent-delete"),
]