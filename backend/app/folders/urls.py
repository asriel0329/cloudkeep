from django.urls import path

from .views import FolderDetailView, FolderListCreateView

urlpatterns = [
    path("", FolderListCreateView.as_view(), name="folder-list-create"),
    path("<int:pk>/", FolderDetailView.as_view(), name="folder-detail"),
]
