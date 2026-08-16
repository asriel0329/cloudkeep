import io

from PIL import Image

from app.celery import app
from app.storage import get_storage

from .models import Blob

THUMBNAIL_SIZE = (256, 256)


@app.task(bind=True, max_retries=3)
def process_uploaded_blob(self, blob_id):
    try:
        blob = Blob.objects.get(pk=blob_id)
    except Blob.DoesNotExist:
        return

    # 這份內容已經處理過了（可能是另一個使用者更早上傳了同樣的內容，
    # 這次只是又有人上傳了一樣的東西、觸發了任務），不用重算一次。
    if blob.processing_status == Blob.STATUS_DONE:
        return

    storage = get_storage()

    try:
        # hash 已經在上傳當下算好了（見 views.py），這裡只需要處理縮圖。
        # 判斷用的是 mime_type——但 mime_type 現在存在 File 上，不是 Blob，
        # 保守起見改成直接嘗試用 Pillow 開檔，開不了就當作不是圖片，跳過。
        try:
            with storage.open(blob.storage_key) as f:
                image = Image.open(f)
                image.load()
                image.thumbnail(THUMBNAIL_SIZE)

                buffer = io.BytesIO()
                image_format = image.format or "PNG"
                image.convert("RGB" if image_format == "JPEG" else image.mode).save(
                    buffer, format=image_format
                )
                buffer.seek(0)

            thumbnail_key = f"thumbnails/{blob.storage_key}"
            storage.save(buffer, thumbnail_key)
            blob.thumbnail_key = thumbnail_key
        except Exception:
            # 不是圖片，或圖片格式 Pillow 不支援，正常情況，不算失敗
            pass

        blob.processing_status = Blob.STATUS_DONE
        blob.save(update_fields=["thumbnail_key", "processing_status"])

    except Exception as exc:
        blob.processing_status = Blob.STATUS_FAILED
        blob.save(update_fields=["processing_status"])
        raise self.retry(exc=exc, countdown=10)