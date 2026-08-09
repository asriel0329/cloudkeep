from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """
    所有儲存後端（Local、S3...）都必須實作這四個方法。
    上層的 Files 模組只透過這個介面操作檔案，完全不知道底層實際上
    是寫進本機硬碟還是雲端物件儲存——這就是之前架構討論提到的
    「Storage 抽象層」，未來要從 Local 換成 S3/MinIO，只需要新增
    一個新的 Backend 類別，Files 模組的程式碼一行都不用改。
    """

    @abstractmethod
    def save(self, file_obj, storage_key: str) -> None:
        """把檔案內容存到 storage_key 這個位置。"""
        raise NotImplementedError

    @abstractmethod
    def open(self, storage_key: str):
        """回傳一個可以讀取檔案內容的檔案物件（binary mode）。"""
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """刪除 storage_key 對應的檔案。"""
        raise NotImplementedError

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """檢查 storage_key 對應的檔案是否存在。"""
        raise NotImplementedError