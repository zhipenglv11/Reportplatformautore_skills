"""
Mortar strength parsing skill.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def parse_mortar_strength(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = context or {}
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")

    # 调试日志
    logger.warning(f"[MORTAR] parse_mortar_strength called with:")
    logger.warning(f"  - project_id: {project_id} (type: {type(project_id)})")
    logger.warning(f"  - node_id: {node_id}")
    logger.warning(f"  - source_node_id: {source_node_id}")
    logger.warning(f"  - context: {context}")

    records = await _fetch_mortar_data(project_id, source_node_id)
    
    # 容错：如果指定了 source_node_id 但查不到数据，尝试不过滤 source_node_id
    if not records and source_node_id and not str(source_node_id).startswith("scope_"):
        logger.warning(f"[MORTAR] No data found with source_node_id={source_node_id}, retrying without node filter...")
        records = await _fetch_mortar_data(project_id, None)
    
    if not records:
        return {
            "dataset_key": "mortar_strength",
            "content": "",
            "table": {"columns": [], "rows": []},
            "meta": {
                "source": "dynamic_db",
                "material_type": "mortar",
                "title": "砂浆强度",
                "has_data": False,
                "warnings": ["未找到砂浆相关的检测数据"],
                "record_count": 0,
                "source_node_id": source_node_id,
            },
        }

    strength_values: List[float] = []
    for record in records:
        strength_values.extend(_extract_strength_values(record))

    if not strength_values:
        return {
            "dataset_key": "mortar_strength",
            "content": "",
            "table": {"columns": [], "rows": []},
            "meta": {
                "source": "dynamic_db",
                "material_type": "mortar",
                "title": "砂浆强度",
                "has_data": False,
                "warnings": ["已检索到砂浆记录，但未提取到强度值"],
                "record_count": len(records),
                "source_node_id": source_node_id,
            },
        }

    avg_strength = round(sum(strength_values) / len(strength_values), 1)
    min_strength = round(min(strength_values), 1)
    max_strength = round(max(strength_values), 1)

    table = _generate_table(records)
    test_method = _infer_test_method(records)

    content = (
        f"依据《贯入法检测砌筑砂浆抗压强度技术规程》（JGJ/T136-2017），采用{test_method}"
        f"检测砌筑砂浆抗压强度，检测结果见表。\n\n"
        f"由上表可知，所测墙体砌筑砂浆抗压强度范围为{min_strength}~{max_strength}MPa。"
    )

    return {
        "dataset_key": "mortar_strength",
        "content": content,
        "table": table,
        "meta": {
            "source": "dynamic_db",
            "material_type": "mortar",
            "title": "砂浆强度",
            "has_data": True,
            "test_count": len(strength_values),
            "record_count": len(records),
            "test_method": test_method,
            "avg_strength": avg_strength,
            "strength_range": {"min": min_strength, "max": max_strength},
            "strength_unit": "MPa",
            "generated_at": datetime.utcnow().isoformat(),
            "source_node_id": source_node_id,
            "warnings": [],
        },
    }


async def _fetch_mortar_data(project_id: str, source_node_id: Optional[str]) -> List[Dict[str, Any]]:
    from models.db import get_engine

    params: Dict[str, Any] = {"pid": project_id, "src": source_node_id}
    node_filter = ""

    if source_node_id and not str(source_node_id).startswith("scope_"):
        node_filter = " AND node_id = :src "

    # scope_mortar_strength 时，按砂浆关键词过滤；否则使用默认 test_item 过滤
    scope_filter = ""
    if source_node_id == "scope_mortar_strength":
        scope_filter = " AND (LOWER(test_item) LIKE '%mortar%' OR test_item LIKE '%砂浆%') "

    sql = f"""
        SELECT
            id,
            node_id,
            test_item,
            test_result,
            strength_estimated_mpa,
            design_strength_grade,
            test_date,
            test_location_text,
            confirmed_result,
            raw_result,
            evidence_refs,
            created_at
        FROM professional_data
        WHERE project_id = :pid
          {node_filter}
          AND (
              LOWER(test_item) LIKE '%mortar%'
              OR test_item = 'mortar_table_recognition'
              OR test_item = 'mortar_strength'
              OR test_item LIKE '%砂浆%'
          )
          {scope_filter}
          AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        ORDER BY created_at DESC
    """

    # 调试日志
    logger.warning(f"[MORTAR] SQL Query: {sql}")
    logger.warning(f"[MORTAR] SQL Params: {params}")
    logger.warning(f"[MORTAR] node_filter: '{node_filter}'")
    logger.warning(f"[MORTAR] scope_filter: '{scope_filter}'")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()

            # Fallback: some projects use inconsistent test_item names.
            # For scope-based mortar extraction, only match mortar-specific signatures.
            if (
                not rows
                and source_node_id == "scope_mortar_strength"
            ):
                fallback_sql = """
                    SELECT
                        id,
                        node_id,
                        test_item,
                        test_result,
                        strength_estimated_mpa,
                        design_strength_grade,
                        test_date,
                        test_location_text,
                        confirmed_result,
                        raw_result,
                        evidence_refs,
                        created_at
                    FROM professional_data
                    WHERE project_id = :pid
                      AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
                       AND (
                            LOWER(CAST(test_item AS TEXT)) LIKE '%mortar%'
                         OR CAST(test_item AS TEXT) LIKE '%砂浆%'
                         OR CAST(confirmed_result AS TEXT) LIKE '%砂浆%'
                         OR CAST(raw_result AS TEXT) LIKE '%砂浆%'
                         OR CAST(confirmed_result AS TEXT) LIKE '%贯入%'
                         OR CAST(raw_result AS TEXT) LIKE '%贯入%'
                         OR LOWER(CAST(confirmed_result AS TEXT)) LIKE '%converted_strength_mpa%'
                         OR LOWER(CAST(raw_result AS TEXT)) LIKE '%converted_strength_mpa%'
                         OR LOWER(CAST(confirmed_result AS TEXT)) LIKE '%single_component_estimated_strength%'
                         OR LOWER(CAST(raw_result AS TEXT)) LIKE '%single_component_estimated_strength%'
                         OR LOWER(CAST(confirmed_result AS TEXT)) LIKE '%mortar_table_recognition%'
                         OR LOWER(CAST(raw_result AS TEXT)) LIKE '%mortar_table_recognition%'
                       )
                    ORDER BY created_at DESC
                """
                rows = conn.execute(text(fallback_sql), {"pid": project_id}).fetchall()
                logger.warning("[MORTAR] Fallback query matched %s rows", len(rows))

        logger.warning(f"[MORTAR] Found {len(rows)} rows")

        out: List[Dict[str, Any]] = []
        for row in rows:
            record = dict(row._mapping)
            record["confirmed_result"] = _parse_json(record.get("confirmed_result"))
            record["raw_result"] = _parse_json(record.get("raw_result"))
            record["evidence_refs"] = _parse_json(record.get("evidence_refs"))
            if _is_mortar_record(record):
                out.append(record)
            else:
                logger.warning(
                    "[MORTAR] Skip non-mortar record: id=%s, node_id=%s, test_item=%s",
                    record.get("id"),
                    record.get("node_id"),
                    record.get("test_item"),
                )
        return out
    except Exception as exc:
        logger.error("fetch mortar data failed: %s", exc, exc_info=True)
        return []


def _parse_json(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _is_mortar_record(record: Dict[str, Any]) -> bool:
    test_item = str(record.get("test_item") or "").lower()
    if any(k in test_item for k in ["mortar", "砂浆", "贯入", "mortar_table_recognition", "mortar_strength"]):
        return True
    if "brick" in test_item or "砖" in test_item:
        return False
    if any(k in test_item for k in ["structure", "damage", "alteration", "拆改", "损伤"]):
        return False
    if test_item:
        return False

    blobs: List[str] = []
    for payload in [record.get("confirmed_result"), record.get("raw_result")]:
        if isinstance(payload, dict):
            try:
                blobs.append(json.dumps(payload, ensure_ascii=False).lower())
            except Exception:
                pass
        elif isinstance(payload, str):
            blobs.append(payload.lower())

    merged = "\n".join(blobs)
    mortar_markers = [
        "砂浆",
        "贯入",
        "mortar_table_recognition",
        "f'_m",
        "f_m",
    ]
    brick_markers = ["brick", "砖强度", "brick_table_recognition"]
    if any(m in merged for m in mortar_markers):
        return True
    if any(m in merged for m in brick_markers):
        return False
    return False


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_strength_values(record: Dict[str, Any]) -> List[float]:
    """
    仅提取“单构件抗压强度推定值”（表格最后一列）用于范围计算。
    不使用换算值、test_result 等其他字段，避免范围口径错误。
    """
    values: List[float] = []

    # Direct columns (仅推定值口径)
    for key in ["strength_estimated_mpa", "estimated_strength_mpa"]:
        v = _to_float(record.get(key))
        if v is not None:
            values.append(v)

    for payload in [record.get("confirmed_result") or {}, record.get("raw_result") or {}]:
        if not isinstance(payload, dict):
            continue

        for key in [
            "estimated_strength_mpa",
            "strength_estimated_mpa",
            "strength_estimated",
            "single_component_estimated_strength_mpa",
            "single_component_strength_estimated_mpa",
            "single_component_estimated_strength",
            "单构件抗压强度推定值",
        ]:
            v = _to_float(payload.get(key))
            if v is not None:
                values.append(v)

        rows = payload.get("rows")
        if isinstance(rows, list):
            for item in rows:
                if not isinstance(item, dict):
                    continue
                for key in [
                    "estimated_strength_mpa",
                    "strength_estimated_mpa",
                    "single_component_estimated_strength_mpa",
                    "single_component_strength_estimated_mpa",
                    "single_component_estimated_strength",
                    "单构件抗压强度推定值",
                ]:
                    v = _to_float(item.get(key))
                    if v is not None:
                        values.append(v)

    # de-dup
    dedup: List[float] = []
    seen = set()
    for v in values:
        k = round(v, 4)
        if k in seen:
            continue
        seen.add(k)
        dedup.append(v)
    return dedup


def _infer_test_method(records: List[Dict[str, Any]]) -> str:
    for record in records:
        test_item = str(record.get("test_item") or "").lower()
        if "mortar" in test_item or "砂浆" in test_item:
            return "砂浆贯入仪"
    return "砂浆贯入仪"


def _extract_location_from_row(item: Dict[str, Any]) -> str:
    for key in ["test_location", "location", "test_position", "位置", "部位"]:
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _pick_float_from_obj(obj: Dict[str, Any], keys: List[str]) -> Optional[float]:
    for key in keys:
        if key in obj:
            v = _to_float(obj.get(key))
            if v is not None:
                return v
    return None


def _extract_converted_estimated(item: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    converted = _pick_float_from_obj(
        item,
        [
            "converted_strength_mpa",
            "strength_converted_mpa",
            "compression_strength_converted_mpa",
            "抗压强度换算值",
            "抗压强度换算值f_m",
            "抗压强度换算值f_m（MPa）",
        ],
    )
    estimated = _pick_float_from_obj(
        item,
        [
            "estimated_strength_mpa",
            "strength_estimated_mpa",
            "single_component_estimated_strength_mpa",
            "single_component_strength_estimated_mpa",
            "single_component_estimated_strength",
            "单构件抗压强度推定值",
            "单构件抗压强度推定值f'_m",
            "单构件抗压强度推定值f'_m（MPa）",
        ],
    )
    return converted, estimated


def _generate_table(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    columns = [
        "序号",
        "轴线部位",
        "抗压强度换算值f_m（MPa）",
        "单构件抗压强度推定值f'_m（MPa）",
    ]

    rows: List[List[Any]] = []
    idx = 1

    for record in records:
        payload = record.get("confirmed_result") or record.get("raw_result") or {}
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            for item in payload["rows"]:
                if not isinstance(item, dict):
                    continue
                converted, estimated = _extract_converted_estimated(item)
                if converted is None and estimated is None:
                    continue
                rows.append([
                    idx,
                    _extract_location_from_row(item),
                    f"{converted:.1f}" if converted is not None else "",
                    f"{estimated:.1f}" if estimated is not None else "",
                ])
                idx += 1
            continue

        # fallback per record
        fallback_obj = payload if isinstance(payload, dict) else {}
        converted, estimated = _extract_converted_estimated(fallback_obj)
        if converted is None and estimated is None:
            converted, estimated = _extract_converted_estimated(record)
        if converted is not None or estimated is not None:
            location = _extract_location_from_row(fallback_obj) or str(record.get("test_location_text") or "")
            rows.append([
                idx,
                location,
                f"{converted:.1f}" if converted is not None else "",
                f"{estimated:.1f}" if estimated is not None else "",
            ])
            idx += 1

    return {"columns": columns, "rows": rows}
