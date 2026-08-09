from .models import Permission


def get_effective_level(user, folder):
    """
    回傳 user 對 folder 的有效權限等級："write" / "read" / None。
    資料夾擁有者一律視為 write。找不到任何授權就回傳 None。
    """

    if folder.owner_id == user.id:
        return Permission.WRITE

    node = folder
    while node is not None:
        perm = Permission.objects.filter(folder=node, user=user).first()
        if perm:
            return perm.level
        node = node.parent

    return None


def has_read_access(user, folder):
    return get_effective_level(user, folder) in (Permission.READ, Permission.WRITE)


def has_write_access(user, folder):
    return get_effective_level(user, folder) == Permission.WRITE