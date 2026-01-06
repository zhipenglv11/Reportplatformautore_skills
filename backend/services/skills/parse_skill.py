from __future__ import annotations

import base64
import json
import uuid
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image
from pdf2image import convert_from_path

from config import settings
from services.llm_gateway.gateway import LLMGateway


class ParseSkill:
    """Vision-first parse: convert to page images and optional LLM call."""

    def __init__(self, llm_gateway: Optional[LLMGateway] = None) -> None:
        self.llm_gateway = llm_gateway

    async def execute(
        self,
        ingest_result: Dict[str, str],
        use_llm: bool = False,
        prompt: Optional[str] = None,
    ) -> Dict[str, object]:
        object_key = ingest_result["object_key"]
        source_hash = ingest_result["source_hash"]

        file_path = Path(object_key)
        suffix = file_path.suffix.lower()

        parse_id = uuid.uuid4().hex
        parsed_dir = Path(settings.parsed_path) / parse_id
        parsed_dir.mkdir(parents=True, exist_ok=True)

        page_images = []
        page_paths = []

        if suffix == ".pdf":
            poppler_path = None
            if settings.poppler_bin_path:
                poppler_bin = Path(settings.poppler_bin_path)
                if not poppler_bin.exists():
                    raise ValueError(f"Poppler bin not found: {poppler_bin}")
                poppler_path = str(poppler_bin)
            images = convert_from_path(str(file_path), poppler_path=poppler_path)
            for idx, img in enumerate(images, start=1):
                page_path = parsed_dir / f"page-{idx}.png"
                img.save(page_path, "PNG")
                page_paths.append(str(page_path))
                page_images.append(self._to_base64_data_url(img))
            file_type = "pdf"
        else:
            img = Image.open(file_path)
            page_path = parsed_dir / "page-1.png"
            img.save(page_path, "PNG")
            page_paths.append(str(page_path))
            page_images.append(self._to_base64_data_url(img))
            file_type = "image"

        evidence_refs = []
        for page_number in range(1, len(page_paths) + 1):
            evidence_refs.append(
                {
                    "object_key": object_key,
                    "type": file_type,
                    "page": page_number,
                    "snippet": "",
                    "source_hash": source_hash,
                }
            )

        result: Dict[str, object] = {
            "parse_id": parse_id,
            "object_key": object_key,
            "source_hash": source_hash,
            "file_type": file_type,
            "page_images": page_images,
            "page_paths": page_paths,
            "evidence_refs": evidence_refs,
            "structured_data": {},
        }

        if use_llm:
            if not self.llm_gateway:
                raise ValueError("LLM gateway is not configured")
            llm_prompt = prompt or "Extract structured data from the document."
            llm_response = await self.llm_gateway.vision_completion(
                provider=settings.llm_provider,
                model=settings.llm_model,
                images=page_images,
                prompt=llm_prompt,
                response_format={"type": "json_object"},
            )
            raw_content = llm_response.get("content", {})
            if isinstance(raw_content, str):
                try:
                    result["structured_data"] = json.loads(raw_content)
                except json.JSONDecodeError:
                    result["structured_data"] = {}
                    result["parse_error"] = "structured_data is not valid JSON"
                    result["structured_data_raw"] = raw_content
            else:
                result["structured_data"] = raw_content
            result["llm_usage"] = llm_response.get("usage", {})

        return result

    @staticmethod
    def _to_base64_data_url(image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
