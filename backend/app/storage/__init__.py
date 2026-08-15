from django.conf import settings
from .local import LocalStorage

def get_storage():
    backend = settings.STORAGE_BACKEND

    if backend == "local":
        return LocalStorage()

    if backend == "s3":
        # 延遲 import，避免 STORAGE_BACKEND=local 時，
        # 因為 boto3 套件的載入而多花不必要的啟動時間。
        from .s3 import S3Storage

        return S3Storage()

    raise ValueError(f"未知的 STORAGE_BACKEND: {backend}")