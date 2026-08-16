from django.db.models import Sum

from .models import File


def get_used_bytes(user):
    """
    計算使用者目前已使用的儲存空間（單位：bytes）。
    先用最直接的方式：把這個使用者名下所有 File 的 size 加總。
    之後 P5-4 做去重偵測時，這個函式的邏輯需要重新設計
    （多個 File 共用同一份 Blob 時，不能重複計入 size），
    先留一個 TODO 提醒未來要回來改。
    """

    total = File.objects.filter(owner=user).aggregate(total=Sum("blob__size"))["total"]
    return total or 0


def has_quota_for(user, additional_bytes):
    """檢查使用者上傳這個大小的檔案後，會不會超過配額。"""
    return get_used_bytes(user) + additional_bytes <= user.storage_quota_bytes