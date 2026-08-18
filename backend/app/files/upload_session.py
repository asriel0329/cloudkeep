import math
import os
import shutil

from django.conf import settings

from .models import UploadSession

# 分塊上傳的暫存區，跟正式的 Storage 抽象層完全分開——不管
# STORAGE_BACKEND 是 local 還是 s3，組裝檔案這件事都需要在本機
# 磁碟上隨機讀寫多個分塊檔案，這件事本身不適合直接對著 S3 做，
# 所以固定用本機暫存，只有「組裝完成的最終內容」才會透過
# get_storage() 存進真正的 Storage。
UPLOAD_TMP_ROOT = os.path.join(settings.MEDIA_ROOT, "upload_sessions")


def _session_dir(session_id):
    return os.path.join(UPLOAD_TMP_ROOT, str(session_id))


def _chunk_path(session_id, chunk_number):
    return os.path.join(_session_dir(session_id), f"{chunk_number}.part")


def create_session(user, folder, filename, mime_type, total_size, chunk_size=5 * 1024 * 1024):
    total_chunks = max(1, math.ceil(total_size / chunk_size))

    session = UploadSession.objects.create(
        owner=user,
        folder=folder,
        filename=filename,
        mime_type=mime_type,
        total_size=total_size,
        chunk_size=chunk_size,
        total_chunks=total_chunks,
        received_chunks=[],
    )

    os.makedirs(_session_dir(session.id), exist_ok=True)
    return session


def save_chunk(session, chunk_number, chunk_file):
    """把一個分塊寫進暫存區，並更新 session 記錄的「已收到」清單。"""

    path = _chunk_path(session.id, chunk_number)
    with open(path, "wb") as destination:
        for piece in chunk_file.chunks():
            destination.write(piece)

    if chunk_number not in session.received_chunks:
        session.received_chunks = sorted(session.received_chunks + [chunk_number])
        session.save(update_fields=["received_chunks", "updated_at"])


def is_complete(session):
    return len(session.received_chunks) == session.total_chunks


def assemble(session):
    """
    把所有分塊按照編號順序接成一個完整檔案，回傳組裝完成後的本機路徑。
    呼叫前一定要先確認 is_complete(session) 是 True。
    """

    assembled_path = os.path.join(_session_dir(session.id), "assembled")

    with open(assembled_path, "wb") as out:
        for i in range(session.total_chunks):
            with open(_chunk_path(session.id, i), "rb") as part:
                while True:
                    data = part.read(65536)
                    if not data:
                        break
                    out.write(data)

    return assembled_path


def cleanup(session):
    """組裝完成、資料已經正式進了 Blob 之後，暫存的分塊檔案就沒用了，整個清掉。"""
    shutil.rmtree(_session_dir(session.id), ignore_errors=True)