from __future__ import annotations

from typing import Dict

from fastapi import UploadFile

from storage.object_storage import get_object_storage


class IngestSkill:
    """Ingest uploaded file into configured storage (local or Supabase)."""

    def __init__(self, storage=None) -> None:
        self.storage = storage or get_object_storage()

    async def execute(self, upload: UploadFile, project_id: str) -> Dict[str, str]:
        result = self.storage.save_upload(upload, project_id)
        return {
            "project_id": project_id,
            "object_key": result["object_key"],
            "source_hash": result["source_hash"],
            "filename": result["filename"],
        }
