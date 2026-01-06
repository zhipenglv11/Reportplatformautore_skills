from __future__ import annotations

from typing import Dict

from fastapi import UploadFile

from storage.object_storage import LocalObjectStorage


class IngestSkill:
    """Ingest uploaded file into local storage."""

    def __init__(self, storage: LocalObjectStorage | None = None) -> None:
        self.storage = storage or LocalObjectStorage()

    async def execute(self, upload: UploadFile, project_id: str) -> Dict[str, str]:
        result = self.storage.save_upload(upload, project_id)
        return {
            "project_id": project_id,
            "object_key": result["object_key"],
            "source_hash": result["source_hash"],
            "filename": result["filename"],
        }
