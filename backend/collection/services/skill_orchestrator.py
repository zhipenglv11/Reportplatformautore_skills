from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from collection.services.skill_registry.registry import SkillRegistry, SkillType
from config import settings
from core.llm.gateway import LLMGateway
from core.tools.pdf_to_image import pdf_to_images


@dataclass
class FileClassification:
    """Structured classification result for an uploaded file."""

    file_name: str
    file_type: str
    skill_name: Optional[str]
    confidence: float
    reasoning: str


@dataclass
class OrchestrationResult:
    """Execution result for a single routed file."""

    file_name: str
    classification: FileClassification
    skill_result: Optional[Dict[str, Any]]
    success: bool
    error: Optional[str] = None


class SkillOrchestrator:
    """Classify uploaded files and route them to the matching skill."""

    _VISION_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    _TEXT_PREVIEW_SUFFIXES = {".txt", ".csv", ".json", ".md"}

    def __init__(
        self,
        llm_gateway: Optional[LLMGateway] = None,
        skill_registry: Optional[SkillRegistry] = None,
    ):
        self.llm_gateway = llm_gateway or LLMGateway()
        self.skill_registry = skill_registry or SkillRegistry()
        self.file_type_to_skill = {
            "concrete": "concrete_table_recognition",
            "mortar": "mortar_table_recognition",
            "brick": "brick_table_recognition",
            "software_result": "software_calculation_recognition",
        }
        self.skill_descriptions = {
            "concrete_table_recognition": "识别并提取混凝土强度检测表格数据",
            "mortar_table_recognition": "识别并提取砂浆强度检测表格数据",
            "brick_table_recognition": "识别并提取砖强度检测表格数据",
            "software_calculation_recognition": "识别并提取软件计算结果参数",
        }
        self._initialize_declarative_skills_if_enabled()

    def _initialize_declarative_skills_if_enabled(self) -> None:
        if not getattr(settings, "enable_declarative_skills", False):
            return

        try:
            self.skill_registry.initialize_declarative_skills(Path(settings.declarative_skills_path))
        except Exception:
            # Classification can still fall back to rule-based routing.
            pass

    @staticmethod
    def _to_base64_data_url(image: Image.Image) -> str:
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def _build_visual_inputs(self, file_path: Path) -> List[str]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            page_images = pdf_to_images(file_path, dpi=120, first_page=1, last_page=2)
            return [self._to_base64_data_url(image) for image in page_images[:2]]

        if suffix in self._VISION_SUFFIXES:
            with Image.open(file_path) as image:
                return [self._to_base64_data_url(image)]

        return []

    def _build_text_preview(self, file_path: Path, file_content_preview: Optional[str]) -> Optional[str]:
        if file_content_preview:
            return file_content_preview[:500]

        if file_path.suffix.lower() not in self._TEXT_PREVIEW_SUFFIXES:
            return None

        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")[:500]
        except Exception:
            return None

    @staticmethod
    def _parse_llm_json_response(response: Dict[str, Any]) -> Dict[str, Any]:
        content = response.get("content")
        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            content = content.strip()
            if not content:
                return {}
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(content[start : end + 1])
                    except json.JSONDecodeError:
                        return {}

        return {}

    async def classify_file(
        self,
        file_path: Path,
        file_name: str,
        file_content_preview: Optional[str] = None,
    ) -> FileClassification:
        """Use the configured LLM to classify a file into a supported skill type."""

        system_prompt = """你是一个专业的文档类型识别助手。你的任务是识别上传文档属于哪一类检测/计算资料，并选择最合适的 skill。

可用 skill：
1. concrete_table_recognition: 混凝土强度检测表
2. mortar_table_recognition: 砂浆强度检测表
3. brick_table_recognition: 砖强度检测表
4. software_calculation_recognition: 软件计算结果

只允许输出 JSON：
{
  "file_type": "concrete|mortar|brick|software_result|other",
  "skill_name": "concrete_table_recognition|mortar_table_recognition|brick_table_recognition|software_calculation_recognition|null",
  "confidence": 0.0,
  "reasoning": "简要理由"
}
"""

        preview = self._build_text_preview(file_path, file_content_preview)
        user_prompt = (
            f"请识别以下文件。\n\n"
            f"文件名: {file_name}\n"
            f"文件路径: {file_path}\n"
            f"文件后缀: {file_path.suffix.lower()}\n"
        )
        if preview:
            user_prompt += f"\n文件内容预览（前500字符）:\n{preview}\n"
        user_prompt += "\n如果是图片或 PDF，请根据版式、表头、字段名称和检测场景识别类型。只返回 JSON。"

        try:
            visual_inputs = self._build_visual_inputs(file_path)
            if visual_inputs:
                response = await self.llm_gateway.vision_completion(
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    images=visual_inputs,
                    prompt=f"{system_prompt}\n\n{user_prompt}",
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )
            else:
                response = await self.llm_gateway.chat_completion(
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )

            result = self._parse_llm_json_response(response)
            file_type = result.get("file_type", "other")
            skill_name = result.get("skill_name")
            if skill_name in {"", "null", "None"}:
                skill_name = None
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")

            if not skill_name and file_type in self.file_type_to_skill:
                skill_name = self.file_type_to_skill[file_type]

            return FileClassification(
                file_name=file_name,
                file_type=file_type,
                skill_name=skill_name,
                confidence=confidence,
                reasoning=reasoning,
            )
        except Exception:
            return self._classify_by_rules(file_name)

    def _classify_by_rules(self, file_name: str) -> FileClassification:
        """Fallback classifier based on filename keywords only."""

        file_name_lower = file_name.lower()

        if any(keyword in file_name_lower for keyword in ["混凝土", "concrete", "回弹", "rebound"]):
            file_type = "concrete"
            skill_name = "concrete_table_recognition"
            confidence = 0.8
            reasoning = "文件名包含混凝土/回弹相关关键词"
        elif any(keyword in file_name_lower for keyword in ["砂浆", "mortar"]):
            file_type = "mortar"
            skill_name = "mortar_table_recognition"
            confidence = 0.8
            reasoning = "文件名包含砂浆相关关键词"
        elif any(keyword in file_name_lower for keyword in ["砖", "brick"]):
            file_type = "brick"
            skill_name = "brick_table_recognition"
            confidence = 0.8
            reasoning = "文件名包含砖相关关键词"
        elif any(keyword in file_name_lower for keyword in ["软件", "software", "计算", "result"]):
            file_type = "software_result"
            skill_name = "software_calculation_recognition"
            confidence = 0.7
            reasoning = "文件名包含软件计算结果相关关键词"
        else:
            file_type = "other"
            skill_name = None
            confidence = 0.3
            reasoning = "无法从文件名识别类型，回退为 other"

        return FileClassification(
            file_name=file_name,
            file_type=file_type,
            skill_name=skill_name,
            confidence=confidence,
            reasoning=reasoning,
        )

    async def orchestrate_files(
        self,
        files: List[Tuple[Path, str]],
        project_id: str,
        node_id: str,
        persist_result: bool = True,
    ) -> List[OrchestrationResult]:
        """Legacy service-level orchestration helper."""

        results: List[OrchestrationResult] = []
        classifications: List[Tuple[Path, str, FileClassification]] = []

        for file_path, file_name in files:
            try:
                classification = await self.classify_file(file_path=file_path, file_name=file_name)
                classifications.append((file_path, file_name, classification))
            except Exception:
                classification = self._classify_by_rules(file_name)
                classifications.append((file_path, file_name, classification))

        skill_groups: Dict[str, List[Tuple[Path, str, FileClassification]]] = {}
        for file_path, file_name, classification in classifications:
            skill_name = classification.skill_name
            if skill_name:
                skill_groups.setdefault(skill_name, []).append((file_path, file_name, classification))
            else:
                results.append(
                    OrchestrationResult(
                        file_name=file_name,
                        classification=classification,
                        skill_result=None,
                        success=False,
                        error=f"未找到匹配的技能，文件类型: {classification.file_type}",
                    )
                )

        for skill_name, file_group in skill_groups.items():
            for file_path, file_name, classification in file_group:
                try:
                    skill_type, executor = self.skill_registry.get_skill(skill_name)
                    if skill_type != SkillType.DECLARATIVE:
                        results.append(
                            OrchestrationResult(
                                file_name=file_name,
                                classification=classification,
                                skill_result=None,
                                success=False,
                                error=f"技能 {skill_name} 不是声明式技能",
                            )
                        )
                        continue

                    script_args = [str(file_path), "--format", "json"]
                    skill_result = await executor.execute(
                        skill_name=skill_name,
                        user_input=f"处理文件: {file_name}",
                        use_llm=False,
                        use_script=True,
                        script_args=script_args,
                    )
                    results.append(
                        OrchestrationResult(
                            file_name=file_name,
                            classification=classification,
                            skill_result=skill_result,
                            success=True,
                        )
                    )
                except Exception as exc:
                    results.append(
                        OrchestrationResult(
                            file_name=file_name,
                            classification=classification,
                            skill_result=None,
                            success=False,
                            error=str(exc),
                        )
                    )

        return results
