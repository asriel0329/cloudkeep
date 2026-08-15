import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from .base import StorageBackend


class S3Storage(StorageBackend):
    """
    透過 boto3 操作 S3 相容的物件儲存（AWS S3 本身，或本機的 MinIO）。
    因為 MinIO 完全相容 S3 的 API 規格，這個類別完全不需要知道自己
    現在連的是哪一個，只是 endpoint_url 不同而已。
    """

    def __init__(self):
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        """
        第一次使用時，如果 bucket 還不存在就自動建立。
        這樣你不用手動先進 MinIO 後台建 bucket，程式會自己處理。
        """
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def save(self, file_obj, storage_key: str) -> None:
        self.client.upload_fileobj(file_obj, self.bucket, storage_key)

    def open(self, storage_key: str):
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        # StreamingBody 本身就有 .read()，FileResponse 可以直接拿來用，
        # 用法跟 LocalStorage 的 open() 回傳的檔案物件一致。
        return response["Body"]

    def delete(self, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_key)

    def exists(self, storage_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=storage_key)
            return True
        except ClientError:
            return False