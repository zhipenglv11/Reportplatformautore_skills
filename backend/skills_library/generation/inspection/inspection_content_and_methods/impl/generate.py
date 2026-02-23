"""
Generate chapter: 鉴定内容和方法及原始记录一览表
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import logging
import yaml

from .extract_utils import extract_instruments_from_db, extract_records_from_db

logger = logging.getLogger(__name__)


def generate_inspection_content_and_methods(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    context supports:
    - use_dynamic_data: bool, default True
    - allow_static_fallback: bool, default True
    - source_node_id/sourceNodeId: real collection node id or scope_*
    - chapter_number: chapter marker
    """
    context = dict(context or {})
    context["project_id"] = project_id
    context["node_id"] = node_id

    fields_config = _load_fields_config()

    section_1 = _generate_section_1(fields_config, context)
    section_2 = _generate_section_2(fields_config, context)
    section_3 = _generate_section_3(fields_config, context)
    sections = [section_1, section_2, section_3]

    has_dynamic_rows = bool((section_2.get("table", {}).get("rows") or []) or (section_3.get("table", {}).get("rows") or []))

    return {
        "chapter_type": "inspection_content_and_methods",
        "chapter_title": "鉴定内容和方法及原始记录一览表",
        "chapter_number": context.get("chapter_number", "三"),
        "has_data": has_dynamic_rows,
        "sections": sections,
        "generation_metadata": {
            "skill_name": "inspection_content_and_methods",
            "skill_version": "1.1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "node_id": node_id,
            "source_node_id": context.get("source_node_id") or context.get("sourceNodeId"),
            "use_dynamic_data": context.get("use_dynamic_data", True),
            "allow_static_fallback": context.get("allow_static_fallback", True),
        },
    }


def _load_fields_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent.parent / "fields.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _generate_section_1(fields_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    section_config = fields_config.get("section_1", {})

    parts = []
    items = section_config.get("items") or []

    if len(items) > 0:
        first = items[0].get("fields") or []
        if len(first) >= 2:
            parts.append(f"1.{first[0].get('content', '')}")
            parts.append(first[1].get("method", ""))

    if len(items) > 1:
        parts.append("\n2.对鉴定对象基础及上部结构进行危险性鉴定，评定鉴定对象基础及楼层的危险性等级。")
        sub_items = items[1].get("sub_items") or []
        if len(sub_items) > 0:
            parts.append(f"\n（1）{sub_items[0].get('content', '')}")
        if len(sub_items) > 1:
            parts.append("\n（2）对鉴定对象上部结构进行危险性鉴定。")
            for step_item in (sub_items[1].get("sub_steps") or []):
                parts.append(f"\n{step_item.get('step', '')} {step_item.get('content', '')}")

    parts.append("\n\n3.综合评定鉴定对象的危险性等级。")
    parts.append("根据现场检查、检测情况及计算结果，按《危险房屋鉴定标准》进行综合分析评定。")

    return {
        "section_number": "(一)",
        "section_title": "鉴定内容和方法",
        "content": "".join(parts),
        "type": "text",
    }


def _generate_section_2(fields_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    section_config = fields_config["section_2"]

    use_dynamic = bool(context.get("use_dynamic_data", True))
    allow_static_fallback = bool(context.get("allow_static_fallback", True))
    project_id = context.get("project_id")
    node_id = context.get("node_id")
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")
    scope_key = source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None

    instruments = []
    data_source = "static"

    if use_dynamic and project_id:
        try:
            instruments = extract_instruments_from_db(
                project_id=project_id,
                node_id=node_id,
                source_node_id=source_node_id,
                scope_key=scope_key,
            )
            data_source = "dynamic"
        except Exception as exc:
            logger.error("dynamic instrument extraction failed: %s", exc, exc_info=True)
            instruments = []
            data_source = "dynamic_error"

    if not instruments and allow_static_fallback:
        instruments = section_config.get("default_instruments", [])
        data_source = "static_fallback"

    return {
        "section_number": "(二)",
        "section_title": "主要检测仪器设备",
        "type": "table",
        "table": {
            "columns": section_config["columns"],
            "rows": instruments,
        },
        "data_source": data_source,
    }


def _generate_section_3(fields_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    section_config = fields_config["section_3"]

    use_dynamic = bool(context.get("use_dynamic_data", True))
    allow_static_fallback = bool(context.get("allow_static_fallback", True))
    project_id = context.get("project_id")
    node_id = context.get("node_id")
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")
    scope_key = source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None

    records = []
    data_source = "static"

    if use_dynamic and project_id:
        try:
            records = extract_records_from_db(
                project_id=project_id,
                node_id=node_id,
                source_node_id=source_node_id,
                scope_key=scope_key,
            )
            data_source = "dynamic"
        except Exception as exc:
            logger.error("dynamic record extraction failed: %s", exc, exc_info=True)
            records = []
            data_source = "dynamic_error"

    if not records and allow_static_fallback:
        records = section_config.get("default_records", [])
        data_source = "static_fallback"

    return {
        "section_number": "(三)",
        "section_title": "原始记录一览表",
        "type": "table",
        "table": {
            "columns": section_config["columns"],
            "rows": records,
        },
        "data_source": data_source,
    }


async def generate_inspection_content_and_methods_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_inspection_content_and_methods(project_id, node_id, context)


if __name__ == "__main__":
    import json

    result = generate_inspection_content_and_methods(
        project_id="test-proj",
        node_id="test-node",
        context={"chapter_number": "三", "use_dynamic_data": True},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
