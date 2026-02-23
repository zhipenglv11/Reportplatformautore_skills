"""
Generate chapter: house overview (房屋概况).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_house_overview": ["delegate_info_recognition", "delegate"],
}


def _parse_json_field(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _resolve_filters(
    node_id: Optional[str],
    source_node_id: Optional[str],
    scope_key: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    effective_scope = scope_key
    effective_node_id = node_id
    if source_node_id:
        if source_node_id.startswith("scope_"):
            effective_scope = source_node_id
            effective_node_id = None
        else:
            effective_node_id = source_node_id
    return effective_node_id, effective_scope


def _build_scope_filter_clause(scope_key: Optional[str]) -> Tuple[str, Dict[str, str]]:
    keywords = SCOPE_TEST_ITEM_KEYWORDS.get(scope_key or "", [])
    if not keywords:
        return "", {}
    clauses: List[str] = []
    params: Dict[str, str] = {}
    for idx, keyword in enumerate(keywords):
        key = f"scope_kw_{idx}"
        clauses.append(f"LOWER(test_item) LIKE :{key}")
        params[key] = f"%{keyword.lower()}%"
    return " OR ".join(clauses), params


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text_value = str(value).strip()
        if text_value:
            return text_value
    return ""


def _pick_value(payload: Dict[str, Any], *paths: str) -> str:
    for path in paths:
        cur: Any = payload
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur.get(part)
            else:
                ok = False
                break
        if ok:
            value = _first_non_empty(cur)
            if value:
                return value
    return ""


def _extract_delegate_payload(
    project_id: str,
    node_id: str,
    source_node_id: Optional[str],
) -> Dict[str, Any]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None,
    )

    engine = get_engine()
    with engine.connect() as conn:
        query_sql = """
            SELECT raw_result, confirmed_result
            FROM professional_data
            WHERE project_id = :pid
              AND test_item = 'delegate_info_recognition'
              AND (:nid IS NULL OR node_id = :nid)
              AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        """
        scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
        if scope_clause:
            query_sql += f"\n              AND ({scope_clause})"
        query_sql += "\n            ORDER BY created_at DESC LIMIT 1"
        row = conn.execute(text(query_sql), {"pid": project_id, "nid": effective_node_id, **scope_params}).fetchone()

    if not row:
        return {}
    data = _parse_json_field(row.confirmed_result) or _parse_json_field(row.raw_result)
    return data if isinstance(data, dict) else {}


def _compose_draft_text(data: Dict[str, Any]) -> str:
    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}

    house_details = _pick_value(data, "house_details", "meta.house_details")
    if house_details:
        return house_details

    house_name = _pick_value(data, "house_name", "鉴定对象", "meta.house_name", "meta.鉴定对象")
    area = _pick_value(data, "building_area", "建筑面积", "meta.building_area", "meta.建筑面积")
    structure = _pick_value(data, "structure_type", "结构类型", "meta.structure_type", "meta.结构类型")
    floors = _pick_value(data, "floor_count", "楼层", "meta.floor_count", "meta.楼层")
    built_year = _pick_value(data, "built_year", "建成年份", "meta.built_year", "meta.建成年份")
    location = _pick_value(data, "address", "房屋地址", "meta.address", "meta.房屋地址")

    parts: List[str] = []
    if location and house_name:
        parts.append(f"鉴定对象{house_name}位于{location}。")
    elif location:
        parts.append(f"鉴定对象位于{location}。")
    elif house_name:
        parts.append(f"鉴定对象为{house_name}。")

    if built_year:
        parts.append(f"据委托方提供资料，鉴定对象约建于{built_year}。")
    if area:
        parts.append(f"建筑面积约为{area}。")
    if floors or structure:
        tail = "，".join([x for x in [floors, structure] if x])
        if tail:
            parts.append(f"房屋结构特征为{tail}。")
    return "".join(parts).strip()


def generate_house_overview(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = dict(context or {})
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")
    data = _extract_delegate_payload(
        project_id=project_id,
        node_id=node_id,
        source_node_id=source_node_id,
    )

    draft_text = _compose_draft_text(data)
    has_data = bool(draft_text)
    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    facts = {
        "house_name": _first_non_empty(meta.get("house_name"), data.get("house_name"), data.get("鉴定对象")),
        "house_details": _first_non_empty(data.get("house_details"), meta.get("house_details")),
        "built_year": _first_non_empty(meta.get("built_year"), data.get("built_year")),
        "building_area": _first_non_empty(meta.get("building_area"), data.get("building_area")),
        "structure_type": _first_non_empty(meta.get("structure_type"), data.get("structure_type")),
        "address": _first_non_empty(meta.get("address"), data.get("address")),
    }

    return {
        "chapter_type": "house_overview",
        "chapter_title": "房屋概况",
        "chapter_number": context.get("chapter_number", "二"),
        "content": draft_text,
        "meta": {
            "dataset_key": "house_overview",
            "title": "房屋概况",
            "has_data": has_data,
            "source": "dynamic_db",
            "source_node_id": source_node_id,
            "facts": facts,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_house_overview_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_house_overview(project_id, node_id, context)

