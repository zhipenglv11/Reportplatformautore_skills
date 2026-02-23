"""
Data extraction utilities for chapter "detailed_inspection".
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_detailed_inspection": [
        "delegate_info_recognition",
        "structure_damage_alterations_recognition",
        "delegate",
        "alteration",
        "damage",
        "inclination",
        "倾斜",
        "沉降",
    ],
}


def extract_delegate_info(
    project_id: str,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    scope_key: Optional[str] = None,
) -> Dict[str, Any]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(node_id, source_node_id, scope_key)
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

        row = conn.execute(
            text(query_sql),
            {"pid": project_id, "nid": effective_node_id, **scope_params},
        ).fetchone()

    if not row:
        return {}

    data = _parse_json_field(row.confirmed_result) or _parse_json_field(row.raw_result)
    if not isinstance(data, dict):
        return {}
    return data


def extract_damage_alteration_items(
    project_id: str,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    scope_key: Optional[str] = None,
) -> List[Dict[str, str]]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(node_id, source_node_id, scope_key)
    rows_out: List[Dict[str, str]] = []

    engine = get_engine()
    with engine.connect() as conn:
        query_sql = """
            SELECT raw_result, confirmed_result
            FROM professional_data
            WHERE project_id = :pid
              AND test_item = 'structure_damage_alterations_recognition'
              AND (:nid IS NULL OR node_id = :nid)
              AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        """
        scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
        if scope_clause:
            query_sql += f"\n              AND ({scope_clause})"
        query_sql += "\n            ORDER BY created_at DESC"

        result = conn.execute(
            text(query_sql),
            {"pid": project_id, "nid": effective_node_id, **scope_params},
        )

        for row in result:
            data = _parse_json_field(row.confirmed_result) or _parse_json_field(row.raw_result)
            if not isinstance(data, dict):
                continue

            items = data.get("items") or []
            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                location = _first_non_empty(
                    item.get("modification_location"),
                    item.get("inspection_location"),
                    item.get("location"),
                )
                desc = _first_non_empty(
                    item.get("modification_description"),
                    item.get("status_description"),
                    item.get("description"),
                )
                photo = _first_non_empty(
                    item.get("photo_no"),
                    item.get("photo"),
                    item.get("photo_reference"),
                )
                if not location and not desc and not photo:
                    continue
                rows_out.append(
                    {
                        "inspection_location": location,
                        "status_description": desc,
                        "photo_reference": _normalize_photo_ref(photo),
                    }
                )

    dedup: Dict[Tuple[str, str, str], Dict[str, str]] = {}
    for row in rows_out:
        key = (
            row.get("inspection_location", ""),
            row.get("status_description", ""),
            row.get("photo_reference", ""),
        )
        if key not in dedup:
            dedup[key] = row
    return list(dedup.values())


def extract_settlement_inclination_text(
    project_id: str,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    scope_key: Optional[str] = None,
) -> str:
    """Try to get user-input/recognized text about settlement and inclination from DB."""
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(node_id, source_node_id, scope_key)

    engine = get_engine()
    with engine.connect() as conn:
        query_sql = """
            SELECT test_item, raw_result, confirmed_result
            FROM professional_data
            WHERE project_id = :pid
              AND (:nid IS NULL OR node_id = :nid)
              AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        """
        scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
        if scope_clause:
            query_sql += f"\n              AND ({scope_clause})"
        query_sql += "\n            ORDER BY created_at DESC"

        result = conn.execute(text(query_sql), {"pid": project_id, "nid": effective_node_id, **scope_params})

        for row in result:
            data = _parse_json_field(row.confirmed_result) or _parse_json_field(row.raw_result)
            if not isinstance(data, dict):
                continue

            text_candidate = _extract_settlement_text_from_payload(data)
            if text_candidate:
                return text_candidate

            test_item = str(row.test_item or "").lower()
            if any(k in test_item for k in ["inclination", "倾斜", "沉降", "settlement"]):
                generic = _first_non_empty(
                    data.get("conclusion"),
                    data.get("summary"),
                    data.get("evaluation"),
                    data.get("result"),
                    data.get("description"),
                )
                if generic:
                    return str(generic).strip()

    return ""


def _extract_settlement_text_from_payload(data: Dict[str, Any]) -> str:
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    for bucket in (data, meta):
        if not isinstance(bucket, dict):
            continue
        text_candidate = _first_non_empty(
            bucket.get("settlement_inclination_observation"),
            bucket.get("settlement_inclination"),
            bucket.get("settlement_observation"),
            bucket.get("inclination_observation"),
            bucket.get("沉降倾斜观测"),
            bucket.get("沉降观测"),
            bucket.get("倾斜观测"),
            bucket.get("沉降及倾斜"),
            bucket.get("沉降情况"),
            bucket.get("倾斜情况"),
        )
        if text_candidate:
            return str(text_candidate).strip()
    return ""


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
        clauses.append("LOWER(test_item) LIKE :" + k)
        params[k] = f"%{keyword.lower()}%"
    return " OR ".join(clauses), params


def _parse_json_field(field_value: Any) -> Dict[str, Any]:
    if not field_value:
        return {}
    if isinstance(field_value, dict):
        return field_value
    if isinstance(field_value, str):
        try:
            return json.loads(field_value)
        except json.JSONDecodeError:
            return {}
    return {}


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text_value = str(value).strip()
        if text_value:
            return text_value
    return ""


def _normalize_photo_ref(value: str) -> str:
    if not value:
        return ""
    text_value = value.replace(" ", "")
    if text_value.startswith("附件"):
        return value
    if text_value.startswith("照片"):
        return f"附件2 {value}"
    return value
