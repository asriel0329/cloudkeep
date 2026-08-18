from django.urls import path

from .views import (
    FolderDetailView,
    FolderDownloadView,
    FolderListCreateView,
    FolderPermanentDeleteView,
    FolderRestoreView,
    FolderTrashListView,
)

urlpatterns = [
    path("", FolderListCreateView.as_view(), name="folder-list-create"),
    path("trash/", FolderTrashListView.as_view(), name="folder-trash-list"),
    path("<int:pk>/", FolderDetailView.as_view(), name="folder-detail"),
    path("<int:pk>/download/", FolderDownloadView.as_view(), name="folder-download"),
    path("<int:pk>/restore/", FolderRestoreView.as_view(), name="folder-restore"),
    path("<int:pk>/permanent/", FolderPermanentDeleteView.as_view(), name="folder-permanent-delete"),
]