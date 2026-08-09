from django.conf import settings

from .local import LocalStorage


def get_storage():
    """
    根據 STORAGE_BACKEND 環境變數決定要用哪個儲存後端。
    Phase 1 目前只有 "local" 這個選項，Phase 4 會加上 "s3"。
    """

    backend = settings.STORAGE_BACKEND

    if backend == "local":
        return LocalStorage()

    raise ValueError(f"未知的 STORAGE_BACKEND: {backend}")