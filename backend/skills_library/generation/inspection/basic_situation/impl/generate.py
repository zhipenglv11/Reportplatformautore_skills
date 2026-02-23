"""
Generate chapter: basic situation (基本情况).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_basic_situation": ["delegate_info_recognition", "delegate"],
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
        k = f"scope_kw_{idx}"
        clauses.append(f"LOWER(test_item) LIKE :{k}")
        params[k] = f"%{keyword.lower()}%"
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
        parts = path.split(".")
        cur: Any = payload
        ok = True
        for part in parts:
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


def generate_basic_situation(
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
    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}

    client_org = _pick_value(
        data,
        "client_org",
        "委托单位",
        "委托方",
        "委托单位名称",
        "meta.client_org",
        "meta.委托单位",
    )
    house_name = _pick_value(
        data,
        "house_name",
        "鉴定对象",
        "房屋名称",
        "meta.house_name",
        "meta.鉴定对象",
    )
    inspection_reason = _pick_value(
        data,
        "inspection_reason",
        "委托鉴定事项",
        "检测原因",
        "meta.inspection_reason",
        "meta.委托鉴定事项",
    )
    acceptance_date = _pick_value(
        data,
        "acceptance_date",
        "受理日期",
        "受理时间",
        "meta.acceptance_date",
        "meta.受理日期",
    )
    inspection_date = _pick_value(
        data,
        "inspection_date",
        "查勘日期",
        "检测日期",
        "meta.inspection_date",
        "meta.查勘日期",
    )

    if not client_org:
        client_org = _first_non_empty(meta.get("client_org"), meta.get("委托单位"))
    if not house_name:
        house_name = _first_non_empty(meta.get("house_name"), meta.get("鉴定对象"))
    if not inspection_reason:
        inspection_reason = _first_non_empty(meta.get("inspection_reason"), meta.get("委托鉴定事项"))
    if not acceptance_date:
        acceptance_date = _first_non_empty(meta.get("acceptance_date"), meta.get("受理日期"))
    if not inspection_date:
        inspection_date = _first_non_empty(meta.get("inspection_date"), meta.get("查勘日期"))

    items = [
        {"label": "委托方", "value": client_org},
        {"label": "鉴定对象", "value": house_name},
        {"label": "委托鉴定事项", "value": inspection_reason},
        {"label": "受理日期", "value": acceptance_date},
        {"label": "查勘日期", "value": inspection_date},
    ]
    has_data = any((item.get("value") or "").strip() for item in items)

    return {
        "chapter_type": "basic_situation",
        "chapter_title": "基本情况",
        "chapter_number": context.get("chapter_number", "一"),
        "items": items,
        "meta": {
            "dataset_key": "basic_situation",
            "title": "基本情况",
            "has_data": has_data,
            "source": "dynamic_db",
            "source_node_id": source_node_id,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_basic_situation_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_basic_situation(project_id, node_id, context)

