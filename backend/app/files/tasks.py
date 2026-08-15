import hashlib
import io

from PIL import Image

from app.celery import app
from app.storage import get_storage

from .models import File

THUMBNAIL_SIZE = (256, 256)

@app.task(bind=True, max_retries=3)
def process_uploaded_file(self, file_id):
    try:
        file_obj = File.objects.get(pk=file_id)
    except File.DoesNotExist:
        return

    storage = get_storage()

    try:
        # 1. 計算 checksum
        hasher = hashlib.sha256()
        with storage.open(file_obj.storage_key) as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        file_obj.hash = hasher.hexdigest()

        # 2. 圖片才產生縮圖
        if file_obj.mime_type.startswith("image/"):
            with storage.open(file_obj.storage_key) as f:
                image = Image.open(f)
                image.load()  # 確保檔案內容完全讀進記憶體，離開 with 區塊後還能用
                image.thumbnail(THUMBNAIL_SIZE)

                buffer = io.BytesIO()
                image_format = image.format or "PNG"
                image.convert("RGB" if image_format == "JPEG" else image.mode).save(
                    buffer, format=image_format
                )
                buffer.seek(0)

            thumbnail_key = f"thumbnails/{file_obj.storage_key}"
            storage.save(buffer, thumbnail_key)
            file_obj.thumbnail_key = thumbnail_key

        file_obj.processing_status = File.STATUS_DONE
        file_obj.save(
            update_fields=["hash", "thumbnail_key", "processing_status", "updated_at"]
        )

    except Exception as exc:
        file_obj.processing_status = File.STATUS_FAILED
        file_obj.save(update_fields=["processing_status", "updated_at"])
        # 重試機制，避免暫時性錯誤（例如 storage 短暫連不上）直接判死刑
        raise self.retry(exc=exc, countdown=10)