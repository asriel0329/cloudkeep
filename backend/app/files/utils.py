import os
import uuid
from django.db import transaction
from django.db.models import F

from .models import Blob

def generate_storage_key(owner_id: int, filename: str) -> str:
    """
    產生檔案在 Storage 裡實際的存放路徑，格式：
        user_<owner_id>/<uuid>.<副檔名>

    用 uuid 而不是直接用原始檔名存，是為了：
    1. 避免特殊字元、超長檔名在檔案系統上造成問題
    2. 避免不同資料夾但同名的檔案，在底層儲存路徑上互相打架
    3. 讓使用者「改檔名」這個操作，完全不用去搬動底層實際的檔案
    """

    ext = os.path.splitext(filename)[1]
    return f"user_{owner_id}/{uuid.uuid4().hex}{ext}"

def release_blob_reference(blob_id):
    """
    File 被永久刪除時呼叫。減少 Blob 的引用計數，
    只有真的沒有人在用這份內容了（歸零），才把 Storage 裡的實際
    檔案跟縮圖一併清掉，並刪除 Blob 這筆記錄。
    """

    from app.storage import get_storage

    with transaction.atomic():
        # select_for_update 鎖住這筆 Blob，避免兩個同時發生的刪除請求
        # 同時把 reference_count 減到負數，或同時誤判「歸零了」。
        blob = Blob.objects.select_for_update().get(pk=blob_id)
        blob.reference_count = F("reference_count") - 1
        blob.save(update_fields=["reference_count"])
        blob.refresh_from_db()

        if blob.reference_count <= 0:
            storage = get_storage()
            storage.delete(blob.storage_key)
            if blob.thumbnail_key:
                storage.delete(blob.thumbnail_key)
            blob.delete()