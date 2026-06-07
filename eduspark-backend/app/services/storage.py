"""文件存储服务 — 抽象接口 + 本地实现"""
import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from app.core.config import get_settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, data: bytes, ext: str, prefix: str = "") -> str:
        """保存文件，返回 storage_key"""
        ...

    @abstractmethod
    def get_url(self, key: str) -> str:
        """获取文件访问 URL"""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除文件"""
        ...


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str = "./storage/files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, ext: str, prefix: str = "") -> str:
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}{ext}" if prefix else f"{uuid.uuid4().hex[:8]}{ext}"
        filepath = self.base_path / filename
        filepath.write_bytes(data)
        return filename

    def get_url(self, key: str) -> str:
        # 开发阶段直接返回本地路径，生产环境通过 API 提供静态文件
        return f"/api/files/{key}"

    def delete(self, key: str) -> bool:
        filepath = self.base_path / key
        if filepath.exists():
            filepath.unlink()
            return True
        return False


class OSSStorage(StorageBackend):
    """阿里云 OSS 存储（生产环境）"""
    def __init__(self):
        self.settings = get_settings()
        # TODO: 初始化 oss2.Bucket

    def save(self, data: bytes, ext: str, prefix: str = "") -> str:
        key = f"{prefix}/{uuid.uuid4().hex[:8]}{ext}" if prefix else f"{uuid.uuid4().hex[:8]}{ext}"
        # self.bucket.put_object(key, data)
        return key

    def get_url(self, key: str) -> str:
        # return self.bucket.sign_url('GET', key, 3600)
        return f"https://{self.settings.OSS_BUCKET}.{self.settings.OSS_ENDPOINT}/{key}"

    def delete(self, key: str) -> bool:
        # self.bucket.delete_object(key)
        return True


def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_TYPE == "oss":
        return OSSStorage()
    return LocalStorage(settings.LOCAL_STORAGE_PATH)
