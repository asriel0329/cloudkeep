import os
import uuid


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