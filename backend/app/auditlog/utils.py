from .models import AuditLog


def log_action(user, action, target_type, target_id, target_name, detail=""):
    """
    寫入一筆操作紀錄。刻意設計成「單一函式呼叫」的形式，
    讓其他模組只要 import 這個函式就能記錄，不用知道 AuditLog 的
    model 細節，之後要改儲存方式（例如換成寫進 Elasticsearch）
    只需要改這個函式內部，呼叫端完全不用動。
    """

    AuditLog.objects.create(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        detail=detail,
    )