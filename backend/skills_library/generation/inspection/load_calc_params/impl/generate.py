"""
Generate chapter: 荷载及计算参数取值.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_load_calc_params": [
        "software_calculation",
        "software_calculation_results",
        "load_calc",
        "荷载",
        "计算参数",
    ],
}

DEFAULTS: Dict[str, Any] = {
    "mortar_strength_mpa": 1.1,
    "brick_strength_grade": "MU10.0",
    "live_loads": {
        "non_accessible_roof": 0.5,
        "living_room_bedroom_kitchen_wc": 2.0,
        "stair_and_balcony": 2.5,
    },
    "dead_loads": {
        "roof": 4.0,
        "floor_prefab": 3.0,
        "stair_room": 6.0,
    },
    "load_combination_type": "1.2D+1.4L",
}


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
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


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


def _normalize_brick_grade(raw: Any) -> str:
    s = str(raw or "").strip().upper().replace(" ", "")
    if not s:
        return DEFAULTS["brick_strength_grade"]
    if s.startswith("MU"):
        num = _to_float(s[2:])
        return f"MU{num:.1f}" if num is not None else s
    num = _to_float(s)
    if num is not None:
        return f"MU{num:.1f}"
    m = re.search(r"MU\s*([0-9]+(?:\.[0-9]+)?)", s)
    if m:
        num = _to_float(m.group(1))
        if num is not None:
            return f"MU{num:.1f}"
    return DEFAULTS["brick_strength_grade"]


def _pick_nested(payload: Dict[str, Any], *paths: str) -> Any:
    for path in paths:
        cur: Any = payload
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur.get(part)
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None


def _extract_payload(
    project_id: str,
    node_id: str,
    source_node_id: Optional[str],
) -> Tuple[Dict[str, Any], Optional[str]]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None,
    )

    base_sql = """
        SELECT test_item, raw_result, confirmed_result, created_at
        FROM professional_data
        WHERE project_id = :pid
          AND (:nid IS NULL OR node_id = :nid)
          AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
          AND (
                LOWER(test_item) LIKE '%software_calculation%'
             OR LOWER(test_item) LIKE '%load_calc%'
             OR test_item LIKE '%荷载%'
             OR test_item LIKE '%计算%'
          )
    """
    scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
    if scope_clause:
        base_sql += f"\n AND ({scope_clause})"
    base_sql += "\n ORDER BY created_at DESC LIMIT 50"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(base_sql),
            {"pid": project_id, "nid": effective_node_id, **scope_params},
        ).fetchall()

    for row in rows:
        confirmed = _parse_json(row.confirmed_result)
        raw = _parse_json(row.raw_result)
        payload = confirmed if isinstance(confirmed, dict) and confirmed else raw
        if isinstance(payload, dict) and payload:
            return payload, str(row.test_item or "")
    return {}, None


def _build_values(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    data = copy.deepcopy(DEFAULTS)
    defaults_applied: List[str] = []

    mortar = _to_float(
        _pick_nested(
            payload,
            "mortar_strength_mpa",
            "mortar_strength",
            "砂浆强度",
            "砌筑砂浆抗压强度取值",
        )
    )
    if mortar is not None:
        data["mortar_strength_mpa"] = mortar
    else:
        defaults_applied.append("mortar_strength_mpa")

    brick_grade_raw = _pick_nested(
        payload,
        "brick_strength_grade",
        "brick_grade",
        "砌墙砖抗压强度等级",
        "块体强度等级",
    )
    if brick_grade_raw is not None:
        data["brick_strength_grade"] = _normalize_brick_grade(brick_grade_raw)
    else:
        defaults_applied.append("brick_strength_grade")

    load_combo = _pick_nested(
        payload,
        "load_combination_type",
        "荷载基本组合类型",
        "combination_type",
    )
    if load_combo:
        data["load_combination_type"] = str(load_combo).strip().upper().replace(" ", "")
    else:
        defaults_applied.append("load_combination_type")

    live_map = {
        "non_accessible_roof": ("live_loads.non_accessible_roof", "活载.不上人屋面", "不上人屋面活载"),
        "living_room_bedroom_kitchen_wc": (
            "live_loads.living_room_bedroom_kitchen_wc",
            "活载.客厅卧室厨房卫生间",
            "客厅卧室厨房卫生间活载",
        ),
        "stair_and_balcony": ("live_loads.stair_and_balcony", "活载.楼梯阳台", "楼梯阳台活载"),
    }
    for key, paths in live_map.items():
        v = _to_float(_pick_nested(payload, *paths))
        if v is not None:
            data["live_loads"][key] = v
        else:
            defaults_applied.append(f"live_loads.{key}")

    dead_map = {
        "roof": ("dead_loads.roof", "恒载.屋面", "屋面恒载"),
        "floor_prefab": ("dead_loads.floor_prefab", "恒载.楼面预制板", "楼面预制板恒载"),
        "stair_room": ("dead_loads.stair_room", "恒载.楼梯间", "楼梯间恒载"),
    }
    for key, paths in dead_map.items():
        v = _to_float(_pick_nested(payload, *paths))
        if v is not None:
            data["dead_loads"][key] = v
        else:
            defaults_applied.append(f"dead_loads.{key}")

    wind = _to_float(_pick_nested(payload, "wind_snow_terrain.basic_wind_pressure", "基本风压"))
    snow = _to_float(_pick_nested(payload, "wind_snow_terrain.basic_snow_pressure", "基本雪压"))
    terrain = _pick_nested(payload, "wind_snow_terrain.terrain_category", "地面粗糙度类别")
    data["wind_snow_terrain"] = {
        "basic_wind_pressure": wind,
        "basic_snow_pressure": snow,
        "terrain_category": str(terrain).strip() if terrain else None,
    }
    return data, sorted(set(defaults_applied))


def _build_table_rows(data: Dict[str, Any]) -> List[List[str]]:
    material_text = (
        f"砌筑砂浆抗压强度取值：{data['mortar_strength_mpa']:.1f}MPa；"
        f"砌墙砖抗压强度等级：{data['brick_strength_grade']}。"
    )
    load_text = (
        f"活载：不上人屋面 {data['live_loads']['non_accessible_roof']:.1f}kN/m²，"
        f"客厅、卧室、厨房、卫生间 {data['live_loads']['living_room_bedroom_kitchen_wc']:.1f}kN/m²，"
        f"楼梯、阳台 {data['live_loads']['stair_and_balcony']:.1f}kN/m²；"
        f"恒载（含自重）：屋面 {data['dead_loads']['roof']:.1f}kN/m²，"
        f"楼面（预制板） {data['dead_loads']['floor_prefab']:.1f}kN/m²，"
        f"楼梯间 {data['dead_loads']['stair_room']:.1f}kN/m²。"
    )
    ws = data.get("wind_snow_terrain") or {}
    if ws.get("basic_wind_pressure") is not None or ws.get("basic_snow_pressure") is not None or ws.get("terrain_category"):
        extra = []
        if ws.get("basic_wind_pressure") is not None:
            extra.append(f"基本风压 {float(ws['basic_wind_pressure']):.2f}kN/m²")
        if ws.get("basic_snow_pressure") is not None:
            extra.append(f"基本雪压 {float(ws['basic_snow_pressure']):.2f}kN/m²")
        if ws.get("terrain_category"):
            extra.append(f"地面粗糙度类别 {ws['terrain_category']}")
        load_text += " " + "，".join(extra) + "。"

    return [
        ["1", "构件截面尺寸", "构件截面尺寸按实测值整理。"],
        ["2", "材料强度", material_text],
        ["3", "荷载取值", load_text],
        ["4", "荷载基本组合类型", f"{data['load_combination_type']}。"],
    ]


def generate_load_calc_params(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = dict(context or {})
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")

    payload, source_test_item = _extract_payload(
        project_id=project_id,
        node_id=node_id,
        source_node_id=source_node_id,
    )
    values, defaults_applied = _build_values(payload if isinstance(payload, dict) else {})

    content = "根据设计图纸及现场检查检测结果，对主体结构采用PKPM进行建模计算，计算参数取值情况见表。"
    table = {
        "columns": ["序号", "主要验算参数", "取值情况"],
        "rows": _build_table_rows(values),
    }

    return {
        "dataset_key": "load_calc_params",
        "content": content,
        "table": table,
        "meta": {
            "title": "荷载及计算参数取值",
            "has_data": True,
            "source": "dynamic_db_with_default_fallback",
            "source_node_id": source_node_id,
            "source_test_item": source_test_item,
            "defaults_applied": defaults_applied,
            "values": values,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_load_calc_params_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_load_calc_params(project_id, node_id, context)
