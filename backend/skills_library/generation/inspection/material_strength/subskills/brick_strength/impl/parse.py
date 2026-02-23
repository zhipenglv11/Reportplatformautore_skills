"""
Brick strength parsing skill.
"""

from __future__ import annotations

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text

logger = logging.getLogger(__name__)


async def parse_brick_strength(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = context or {}
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")

    # 调试日志
    logger.warning(f"[BRICK] parse_brick_strength called with:")
    logger.warning(f"  - project_id: {project_id} (type: {type(project_id)})")
    logger.warning(f"  - node_id: {node_id}")
    logger.warning(f"  - source_node_id: {source_node_id}")
    logger.warning(f"  - context: {context}")

    records = await _fetch_brick_data(project_id, source_node_id)
    
    # 容错：如果指定了 source_node_id 但查不到数据，尝试不过滤 source_node_id
    if not records and source_node_id and not str(source_node_id).startswith("scope_"):
        logger.warning(f"[BRICK] No data found with source_node_id={source_node_id}, retrying without node filter...")
        records = await _fetch_brick_data(project_id, None)
    
    if not records:
        return {
            "dataset_key": "brick_strength",
            "content": "",
            "table": {"columns": [], "rows": []},
            "meta": {
                "source": "dynamic_db",
                "material_type": "brick",
                "title": "砖强度",
                "has_data": False,
                "warnings": ["未找到砖相关的检测数据"],
                "record_count": 0,
                "source_node_id": source_node_id,
            },
        }

    strength_values: List[float] = []
    for record in records:
        strength_values.extend(_extract_strength_values(record))

    if not strength_values:
        return {
            "dataset_key": "brick_strength",
            "content": "",
            "table": {"columns": [], "rows": []},
            "meta": {
                "source": "dynamic_db",
                "material_type": "brick",
                "title": "砖强度",
                "has_data": False,
                "warnings": ["已检索到砖记录，但未提取到强度值"],
                "record_count": len(records),
                "source_node_id": source_node_id,
            },
        }

    avg_strength = round(sum(strength_values) / len(strength_values), 1)
    min_strength = round(min(strength_values), 1)
    max_strength = round(max(strength_values), 1)

    table = _generate_table(records)
    test_method = "回弹法"

    content = (
        "依据《砌体工程现场检测技术标准》（GB/T50315-2011），采用回弹法检测砌体砖抗压强度，检测结果见表。"
        f"\n\n由上表可知，所测墙体烧结砖抗压强度范围为{min_strength}~{max_strength}MPa。"
    )

    return {
        "dataset_key": "brick_strength",
        "content": content,
        "table": table,
        "meta": {
            "source": "dynamic_db",
            "material_type": "brick",
            "title": "砖强度",
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


async def _fetch_brick_data(project_id: str, source_node_id: Optional[str]) -> List[Dict[str, Any]]:
    from models.db import get_engine

    params: Dict[str, Any] = {"pid": project_id, "src": source_node_id}
    node_filter = ""

    if source_node_id and not str(source_node_id).startswith("scope_"):
        node_filter = " AND node_id = :src "

    scope_filter = ""
    if source_node_id == "scope_brick_strength":
        scope_filter = " AND (LOWER(test_item) LIKE '%brick%' OR test_item LIKE '%砖%') "

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
              LOWER(test_item) LIKE '%brick%'
              OR test_item = 'brick_table_recognition'
              OR test_item = 'brick_strength'
              OR test_item LIKE '%砖%'
          )
          {scope_filter}
          AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        ORDER BY created_at DESC
    """

    # 调试日志
    logger.warning(f"[BRICK] SQL Query: {sql}")
    logger.warning(f"[BRICK] SQL Params: {params}")
    logger.warning(f"[BRICK] node_filter: '{node_filter}'")
    logger.warning(f"[BRICK] scope_filter: '{scope_filter}'")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()

        logger.warning(f"[BRICK] Found {len(rows)} rows")

        out: List[Dict[str, Any]] = []
        for row in rows:
            record = dict(row._mapping)
            record["confirmed_result"] = _parse_json(record.get("confirmed_result"))
            record["raw_result"] = _parse_json(record.get("raw_result"))
            record["evidence_refs"] = _parse_json(record.get("evidence_refs"))
            out.append(record)
        return out
    except Exception as exc:
        logger.error("fetch brick data failed: %s", exc, exc_info=True)
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


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_strength_values(record: Dict[str, Any]) -> List[float]:
    values: List[float] = []

    for key in ["strength_estimated_mpa", "test_result"]:
        v = _to_float(record.get(key))
        if v is not None:
            values.append(v)

    for payload in [record.get("confirmed_result") or {}, record.get("raw_result") or {}]:
        if not isinstance(payload, dict):
            continue

        for key in [
            "strength_estimated_mpa",
            "strength_estimated",
            "rebound_strength",
            "estimated_strength_mpa",
            "test_result",
        ]:
            v = _to_float(payload.get(key))
            if v is not None:
                values.append(v)

        rows = payload.get("rows")
        if isinstance(rows, list):
            for item in rows:
                if not isinstance(item, dict):
                    continue
                for key in ["estimated_strength_mpa", "strength_estimated_mpa", "rebound_strength"]:
                    v = _to_float(item.get(key))
                    if v is not None:
                        values.append(v)

    dedup: List[float] = []
    seen = set()
    for v in values:
        k = round(v, 4)
        if k in seen:
            continue
        seen.add(k)
        dedup.append(v)
    return dedup


def _extract_location_from_row(item: Dict[str, Any]) -> str:
    for key in ["test_location", "location", "test_position", "位置", "部位"]:
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _generate_table(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    columns = ["序号", "轴线部位", "砖抗压强度推定值（MPa）"]
    rows: List[List[Any]] = []
    idx = 1

    for record in records:
        payload = record.get("confirmed_result") or record.get("raw_result") or {}
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            for item in payload["rows"]:
                if not isinstance(item, dict):
                    continue
                val = None
                for key in ["estimated_strength_mpa", "strength_estimated_mpa", "rebound_strength"]:
                    val = _to_float(item.get(key))
                    if val is not None:
                        break
                if val is None:
                    continue
                rows.append([idx, _extract_location_from_row(item), f"{val:.1f}"])
                idx += 1
            continue

        vals = _extract_strength_values(record)
        if vals:
            rows.append([idx, str(record.get("test_location_text") or ""), f"{vals[0]:.1f}"])
            idx += 1

    return {"columns": columns, "rows": rows}
