# -*- coding: utf-8 -*-
"""
Supabase Storage 适配器：用于 Railway 等无持久化磁盘的云部署。
使用 Supabase Storage REST API（通过 httpx），无需 supabase-py SDK。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict

import httpx
from fastapi import UploadFile

from config import settings


class SupabaseObjectStorage:
    """将上传文件存储到 Supabase Storage Bucket。"""

    def __init__(self) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "Supabase Storage 需要配置 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 环境变量"
            )
        self.base_url = settings.supabase_url.rstrip("/")
        self.key = settings.supabase_service_role_key
        self.bucket = settings.supabase_storage_bucket

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.key}"}

    def save_upload(self, upload: UploadFile, project_id: str) -> Dict[str, str]:
        """将文件上传至 Supabase Storage，返回元数据（含公开 URL 作为 object_key）。"""
        upload.file.seek(0)
        content = upload.file.read()

        hasher = hashlib.sha256()
        hasher.update(content)
        file_hash = hasher.hexdigest()

        filename = Path(upload.filename or "unknown").name
        storage_path = f"{project_id}/{filename}"

        upload_url = (
            f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        )
        content_type = upload.content_type or "application/octet-stream"

        resp = httpx.put(
            upload_url,
            content=content,
            headers={
                **self._auth_headers(),
                "Content-Type": content_type,
                "x-upsert": "true",
            },
            timeout=60,
        )
        resp.raise_for_status()

        public_url = (
            f"{self.base_url}/storage/v1/object/public/{self.bucket}/{storage_path}"
        )

        upload.file.seek(0)
        return {
            "object_key": public_url,
            "source_hash": file_hash,
            "filename": filename,
        }
