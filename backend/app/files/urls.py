from django.urls import path

from .views import FileDetailView, FileDownloadView, FileListView, FileUploadView

urlpatterns = [
    path("", FileListView.as_view(), name="file-list"),
    path("upload/", FileUploadView.as_view(), name="file-upload"),
    path("<int:pk>/", FileDetailView.as_view(), name="file-detail"),
    path("<int:pk>/download/", FileDownloadView.as_view(), name="file-download"),
]