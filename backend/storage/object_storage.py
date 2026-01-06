from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict

from fastapi import UploadFile

from config import settings


class LocalObjectStorage:
    """Local filesystem storage for Phase 0."""

    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = Path(base_path) if base_path else Path(settings.storage_base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_upload(self, upload: UploadFile, project_id: str) -> Dict[str, str]:
        """Save an uploaded file and return metadata."""
        project_dir = self.base_path / "uploads" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(upload.filename or "unknown").name
        target_path = project_dir / filename

        hasher = hashlib.sha256()
        
        # 重置文件指针到开始位置（如果之前读取过）
        upload.file.seek(0)
        
        with target_path.open("wb") as f:
            while True:
                chunk = upload.file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                hasher.update(chunk)
                f.write(chunk)

        file_hash = hasher.hexdigest()
        
        # 重置文件指针，以便后续可能的使用
        upload.file.seek(0)

        return {
            "object_key": str(target_path),
            "source_hash": file_hash,
            "filename": filename,
        }
