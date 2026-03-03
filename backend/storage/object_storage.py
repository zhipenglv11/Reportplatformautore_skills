from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Union

from fastapi import UploadFile

from config import settings


class LocalObjectStorage:
    """本地文件系统存储，适用于开发环境（storage_backend=local）。"""

    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path) if base_path else Path(settings.storage_base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile, project_id: str) -> Dict[str, str]:
        """保存上传文件到本地，返回文件元数据。"""
        project_dir = self.base_path / "uploads" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(upload.filename or "unknown").name
        target_path = project_dir / filename

        hasher = hashlib.sha256()
        upload.file.seek(0)

        with target_path.open("wb") as f:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
                f.write(chunk)

        file_hash = hasher.hexdigest()
        upload.file.seek(0)

        return {
            "object_key": str(target_path),
            "source_hash": file_hash,
            "filename": filename,
        }


def get_object_storage() -> Union[LocalObjectStorage, "SupabaseObjectStorage"]:
    """根据配置返回合适的存储后端实例。"""
    if settings.storage_backend == "supabase":
        from storage.supabase_storage import SupabaseObjectStorage
        return SupabaseObjectStorage()
    return LocalObjectStorage()
