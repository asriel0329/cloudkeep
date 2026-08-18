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
    FileVersionDownloadView,
    FileVersionRestoreView,
    FileVersionListView,
    StorageQuotaView,
    UploadCompleteView,
    UploadSessionInitView,
    UploadSessionStatusView,
    UploadChunkView,
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
    path("<int:pk>/versions/", FileVersionListView.as_view(), name="file-version-list"),
    path("<int:pk>/versions/<int:version_number>/restore/", FileVersionRestoreView.as_view(), name="file-version-restore"),
    path("<int:pk>/versions/<int:version_number>/download/", FileVersionDownloadView.as_view(), name="file-version-download"),
    path("upload/sessions/", UploadSessionInitView.as_view(), name="upload-session-init"),
    path("upload/sessions/<uuid:session_id>/", UploadSessionStatusView.as_view(), name="upload-session-status"),
    path("upload/sessions/<uuid:session_id>/chunks/<int:chunk_number>/", UploadChunkView.as_view(), name="upload-chunk"),
    path("upload/sessions/<uuid:session_id>/complete/", UploadCompleteView.as_view(), name="upload-complete"),
]