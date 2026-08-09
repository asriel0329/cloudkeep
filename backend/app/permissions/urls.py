from django.urls import path

from .views import PermissionListCreateView, PermissionRevokeView, SharedWithMeView

urlpatterns = [
    path("", PermissionListCreateView.as_view(), name="permission-list-create"),
    path("<int:pk>/", PermissionRevokeView.as_view(), name="permission-revoke"),
    path("shared-with-me/", SharedWithMeView.as_view(), name="shared-with-me"),
]