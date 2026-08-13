from django.urls import path

from .views import FileDetailView, FileDownloadView, FileListView, FileThumbnailView, FileUploadView

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("<int:pk>/", FileDetailView.as_view(), name="file-detail"),
    path("<int:pk>/download/", FileDownloadView.as_view(), name="file-download"),
    path("<int:pk>/thumbnail/", FileThumbnailView.as_view(), name="file-thumbnail"),
]