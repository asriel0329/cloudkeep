import os

from django.conf import settings

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """
    Phase 1 使用的儲存後端：直接寫進本機硬碟的 MEDIA_ROOT 資料夾。
    之後 Phase 4 會新增 S3Storage，兩者都遵守 StorageBackend 這個
    共同介面，Files 模組完全不用知道現在用的是哪一個。
    """

    def __init__(self):
        self.root = settings.MEDIA_ROOT

    def _full_path(self, storage_key: str) -> str:
        return os.path.join(self.root, storage_key)

    def save(self, file_obj, storage_key: str) -> None:
        full_path = self._full_path(storage_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

    def open(self, storage_key: str):
        return open(self._full_path(storage_key), "rb")

    def delete(self, storage_key: str) -> None:
        full_path = self._full_path(storage_key)
        if os.path.exists(full_path):
            os.remove(full_path)

    def exists(self, storage_key: str) -> bool:
        return os.path.exists(self._full_path(storage_key))