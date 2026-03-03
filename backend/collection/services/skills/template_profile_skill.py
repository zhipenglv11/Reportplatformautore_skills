from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Optional

from config import settings
from core.llm.gateway import LLMGateway


class TemplateProfileSkill:
    """Extract table headers and compute fingerprint."""

    def __init__(self, llm_gateway: LLMGateway) -> None:
        self.llm_gateway = llm_gateway

    async def execute(self, images: List[str]) -> Dict[str, object]:
        prompt = (
            "你是表格解析助手，只输出JSON。\\n"
            "任务：从图片中识别表头列名与标题，不要抽取业务字段。\\n"
            "输出字段：\\n"
            "- title: 表名/标题（可空）\\n"
            "- headers: 列名数组（按从左到右顺序）\\n"
            "- header_row_text: 你识别到的表头原文（可空）\\n"
            "- record_code: ????????????????????\n"
            "仅输出JSON对象。"
        )
        response = await self.llm_gateway.vision_completion(
            provider=settings.llm_provider,
            model=settings.llm_model,
            images=images,
            prompt=prompt,
            response_format={"type": "json_object"},
        )
        content = response.get("content", {}) if isinstance(response, dict) else {}
        title = content.get("title") if isinstance(content, dict) else None
        headers = content.get("headers") if isinstance(content, dict) else None
        header_row_text = content.get("header_row_text") if isinstance(content, dict) else None
        record_code = content.get("record_code") if isinstance(content, dict) else None
        headers = headers if isinstance(headers, list) else []

        normalized = [self._normalize_header(h) for h in headers if isinstance(h, str)]
        fingerprint = self._fingerprint(normalized)

        return {
            "title": title,
            "headers": headers,
            "headers_normalized": normalized,
            "header_row_text": header_row_text,
            "record_code": record_code,
            "fingerprint": fingerprint,
        }

    @staticmethod
    def _normalize_header(value: str) -> str:
        text = value.strip().lower()
        text = re.sub(r"\\s+", "", text)
        text = re.sub(r"[^0-9a-z\\u4e00-\\u9fff]+", "", text)
        return text

    @staticmethod
    def _fingerprint(headers: List[str]) -> str:
        joined = "|".join(headers)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()
