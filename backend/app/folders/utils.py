from django.utils import timezone


def cascade_soft_delete(folder):
    """
    刪除一個資料夾時，底下所有子資料夾、檔案都要一起進回收桶，
    不然會出現「資料夾被刪了，但裡面的檔案卻還留在正常列表」
    這種不一致的狀態。用遞迴走過整棵子樹。
    """

    now = timezone.now()
    folder.is_deleted = True
    folder.deleted_at = now
    folder.save(update_fields=["is_deleted", "deleted_at"])

    folder.files.filter(is_deleted=False).update(is_deleted=True, deleted_at=now)

    for child in folder.children.filter(is_deleted=False):
        cascade_soft_delete(child)


def cascade_restore(folder):
    """還原一個資料夾時，一併還原底下的子資料夾與檔案。"""

    folder.is_deleted = False
    folder.deleted_at = None
    folder.save(update_fields=["is_deleted", "deleted_at"])

    folder.files.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)

    for child in folder.children.filter(is_deleted=True):
        cascade_restore(child)