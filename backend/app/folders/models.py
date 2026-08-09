from django.conf import settings
from django.db import models


class Folder(models.Model):
    """
    資料夾 model，用 parent 欄位指向自己（self-relation）來表示樹狀結構，
    這就是之前架構討論提過的「adjacency list」設計：

        根目錄（parent=None）
        └── Project A（parent=根目錄的 id）
            └── Docs（parent=Project A 的 id）

    優點：新增/刪除/查「某資料夾底下有哪些子項目」都很簡單快速。
    缺點：查「某資料夾的完整路徑」（例如 /Project A/Docs）要遞迴往上找，
    但 Phase 1 資料量小，這個缺點還不會構成問題，之後真的需要效能
    優化時再考慮 materialized path 之類的替代設計。
    """

    name = models.CharField(max_length=255)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="folders",
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text="父資料夾。null 代表這是使用者的根目錄下的第一層資料夾。",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 同一個使用者、同一個父資料夾底下，不能有兩個同名資料夾
        # （跟平常在自己電腦資料夾裡體驗一致：同層不能重名）
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "parent", "name"],
                name="unique_folder_name_per_parent",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name
