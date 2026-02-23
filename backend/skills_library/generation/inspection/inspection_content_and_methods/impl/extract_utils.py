"""
Utilities for generating "inspection_content_and_methods" chapter tables.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

logger = logging.getLogger(__name__)


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_concrete_strength": ["混凝土", "回弹", "concrete", "rebound"],
    "scope_mortar_strength": ["砂浆", "mortar"],
    "scope_brick_strength": ["砖", "brick"],
    "scope_steel_hardness": ["钢", "里氏", "steel", "hardness"],
}

INSTRUMENT_TYPE_MAPPING: Dict[str, Dict[str, str]] = {
    "砖": {"name": "测砖回弹仪", "default_model": "ZC4"},
    "brick": {"name": "测砖回弹仪", "default_model": "ZC4"},
    "砂浆": {"name": "贯入式砂浆强度检测仪", "default_model": "SJY-800B"},
    "mortar": {"name": "贯入式砂浆强度检测仪", "default_model": "SJY-800B"},
    "混凝土": {"name": "回弹仪", "default_model": "HT-225"},
    "concrete": {"name": "回弹仪", "default_model": "HT-225"},
    "rebound": {"name": "回弹仪", "default_model": "HT-225"},
    "钢筋": {"name": "钢筋扫描仪", "default_model": "PROFOMETER-6"},
    "steel": {"name": "钢筋扫描仪", "default_model": "PROFOMETER-6"},
    "倾斜": {"name": "手持式激光测距仪", "default_model": "GLM40"},
    "tilt": {"name": "手持式激光测距仪", "default_model": "GLM40"},
    "delegate_info": {"name": "手持式激光测距仪", "default_model": "GLM40"},
    "尺寸": {"name": "钢卷尺", "default_model": "5M"},
    "ruler": {"name": "钢卷尺", "default_model": "5M"},
}

RECORD_NAME_MAPPING: Dict[str, str] = {
    "KJQR-056-2047": "结构布置检查原始记录",
    "KJQR-056-2048": "结构构件拆改检查原始记录",
    "KJQR-056-206": "贯入法检测砂浆强度原始记录",
    "KJQR-056-223": "砖回弹原始记录",
    "KJQR-056-215": "混凝土回弹检测原始记录",
    "KSQR-4.13-XC-10": "混凝土强度检测原始记录",
    "砂浆": "贯入法检测砂浆强度原始记录",
    "砖": "砖回弹原始记录",
    "混凝土": "混凝土回弹检测原始记录",
    "倾斜": "倾斜测量检测原始记录",
    "PKPM": "PKPM计算原始记录",
    "拆改": "结构构件拆改检查原始记录",
    "布置": "结构布置检查原始记录",
    "mortar_table_recognition": "贯入法检测砂浆强度原始记录",
    "brick_table_recognition": "砖回弹原始记录",
    "concrete_table_recognition": "混凝土回弹检测原始记录",
    "structure_damage_alterations_recognition": "结构构件拆改检查原始记录",
}


def extract_instruments_from_db(
    project_id: str,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    scope_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(node_id, source_node_id, scope_key)
    instruments_dict: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    try:
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
                query_sql += f"\n                  AND ({scope_clause})"
            query_sql += "\n                ORDER BY created_at"

            result = conn.execute(text(query_sql), {"pid": project_id, "nid": effective_node_id, **scope_params})

            for row in result:
                test_item = row.test_item or ""
                raw_result = _parse_json_field(row.raw_result)
                confirmed_result = _parse_json_field(row.confirmed_result)

                instrument_info = _extract_instrument_info(test_item, raw_result, confirmed_result)
                if not instrument_info:
                    continue

                key = (
                    instrument_info.get("instrument_name", ""),
                    instrument_info.get("model", ""),
                    instrument_info.get("serial_number", ""),
                )
                if key not in instruments_dict:
                    instruments_dict[key] = instrument_info

        rows = list(instruments_dict.values())
        rows.sort(key=lambda x: x.get("instrument_name", ""))
        return rows
    except Exception as exc:
        logger.error("extract_instruments_from_db failed: %s", exc, exc_info=True)
        return []


def extract_records_from_db(
    project_id: str,
    node_id: Optional[str] = None,
    source_node_id: Optional[str] = None,
    scope_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(node_id, source_node_id, scope_key)
    records_dict: Dict[Tuple[str, str], Dict[str, Any]] = {}

    try:
        engine = get_engine()
        with engine.connect() as conn:
            query_sql = """
                SELECT test_item, raw_result, confirmed_result, record_code
                FROM professional_data
                WHERE project_id = :pid
                  AND (:nid IS NULL OR node_id = :nid)
                  AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
            """
            scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
            if scope_clause:
                query_sql += f"\n                  AND ({scope_clause})"
            query_sql += "\n                ORDER BY created_at"

            result = conn.execute(text(query_sql), {"pid": project_id, "nid": effective_node_id, **scope_params})

            for row in result:
                test_item = row.test_item or ""
                record_code = row.record_code
                raw_result = _parse_json_field(row.raw_result)
                confirmed_result = _parse_json_field(row.confirmed_result)

                record_info = _extract_record_info(test_item, raw_result, confirmed_result, record_code)
                if record_info and record_info.get("internal_number"):
                    key = (str(record_info.get("record_name") or ""), str(record_info.get("internal_number") or ""))
                    if key not in records_dict:
                        records_dict[key] = record_info

        rows = list(records_dict.values())
        rows.sort(key=lambda x: (x.get("record_name", ""), x.get("internal_number", "")))
        return rows
    except Exception as exc:
        logger.error("extract_records_from_db failed: %s", exc, exc_info=True)
        return []


def _resolve_filters(node_id: Optional[str], source_node_id: Optional[str], scope_key: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
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


def _extract_instrument_info(test_item: str, raw_result: Dict[str, Any], confirmed_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = confirmed_result if confirmed_result else raw_result
    meta = data.get("meta", {}) if isinstance(data, dict) else {}

    test_item_lc = (test_item or "").lower()
    instrument_config = None
    for key, config in INSTRUMENT_TYPE_MAPPING.items():
        if key.lower() in test_item_lc:
            instrument_config = config
            break

    model = (
        meta.get("instrument_model")
        or meta.get("仪器型号")
        or data.get("instrument_model")
        or data.get("仪器型号")
        or (instrument_config["default_model"] if instrument_config else "")
    )
    serial_number = (
        meta.get("instrument_id")
        or meta.get("仪器编号")
        or data.get("instrument_id")
        or data.get("仪器编号")
        or ""
    )

    instrument_name = (
        (instrument_config or {}).get("name")
        or meta.get("instrument_name")
        or meta.get("检测仪器")
        or data.get("instrument_name")
        or data.get("检测仪器")
        or _infer_instrument_name_from_model(model)
        or "检测仪器"
    )

    if not model and not serial_number:
        return None

    return {
        "instrument_name": instrument_name,
        "model": model,
        "serial_number": serial_number,
        "valid_until": None,
    }


def _infer_instrument_name_from_model(model: str) -> str:
    m = (model or "").upper()
    if not m:
        return ""
    if "SJY" in m:
        return "贯入式砂浆强度检测仪"
    if "ZC" in m or "HT" in m:
        return "回弹仪"
    if "PROFOMETER" in m:
        return "钢筋扫描仪"
    if "GLM" in m:
        return "手持式激光测距仪"
    return ""


def _extract_record_info(test_item: str, raw_result: Dict[str, Any], confirmed_result: Dict[str, Any], record_code: Optional[str]) -> Optional[Dict[str, Any]]:
    data = confirmed_result if confirmed_result else raw_result
    meta = data.get("meta", {}) if isinstance(data, dict) else {}

    record_no = _pick_first_non_empty([
        meta.get("internal_number"), meta.get("internal_no"), meta.get("record_no"), meta.get("record_code"),
        meta.get("记录编号"), meta.get("内部编号"),
        data.get("internal_number"), data.get("internal_no"), data.get("record_no"), data.get("record_code"),
        data.get("记录编号"), data.get("内部编号"),
        record_code,
    ])
    record_no = _normalize_record_identifier(record_no)
    if not record_no:
        return None

    return {
        "record_name": _infer_record_name(test_item, data),
        "internal_number": record_no,
    }


def _infer_record_name(test_item: str, data: Dict[str, Any]) -> str:
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    control_id = meta.get("control_id") or meta.get("控制编号") or data.get("table_id") or ""
    if control_id in RECORD_NAME_MAPPING:
        return RECORD_NAME_MAPPING[control_id]
    for keyword, name in RECORD_NAME_MAPPING.items():
        if keyword in (test_item or "") or keyword in control_id:
            return name
    return f"{test_item}原始记录"


def _pick_first_non_empty(values: List[Any]) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_record_identifier(value: str) -> str:
    if not value:
        return ""
    text = str(value).strip()
    text = text.replace("：", ":").replace("～", "~")
    text = re.sub(r"\s*:\s*", ":", text)
    text = re.sub(r"\s*~\s*", "~", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
