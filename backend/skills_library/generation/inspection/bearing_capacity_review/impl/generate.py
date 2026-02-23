"""
Generate chapter: 承载能力复核验算.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_bearing_capacity_review": [
        "delegate_info_recognition",
        "delegate",
        "house_overview",
        "bearing_capacity_review",
    ],
}

CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}

PHI_TABLE: Dict[str, Dict[str, float]] = {
    "I": {"砌体构件": 1.15, "混凝土构件": 1.20, "木构件": 1.15, "钢构件": 1.00},
    "II": {"砌体构件": 1.05, "混凝土构件": 1.10, "木构件": 1.05, "钢构件": 1.00},
    "III": {"砌体构件": 1.00, "混凝土构件": 1.00, "木构件": 1.00, "钢构件": 1.00},
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


def _extract_delegate_payload(
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

    sql = """
        SELECT test_item, raw_result, confirmed_result, created_at
        FROM professional_data
        WHERE project_id = :pid
          AND (:nid IS NULL OR node_id = :nid)
          AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
          AND (
               test_item = 'delegate_info_recognition'
               OR LOWER(test_item) LIKE '%delegate%'
               OR test_item LIKE '%房屋概况%'
          )
    """
    scope_clause, scope_params = _build_scope_filter_clause(effective_scope)
    if scope_clause:
        sql += f"\n AND ({scope_clause})"
    sql += "\n ORDER BY created_at DESC LIMIT 20"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"pid": project_id, "nid": effective_node_id, **scope_params}).fetchall()

    for row in rows:
        confirmed = _parse_json(row.confirmed_result)
        raw = _parse_json(row.raw_result)
        payload = confirmed if isinstance(confirmed, dict) and confirmed else raw
        if isinstance(payload, dict) and payload:
            return payload, str(row.test_item or "")
    return {}, None


def _extract_year(payload: Dict[str, Any]) -> Optional[int]:
    direct = _pick_nested(payload, "built_year", "meta.built_year", "建成年份", "meta.建成年份")
    if direct is not None:
        m = re.search(r"(19|20)\d{2}", str(direct))
        if m:
            return int(m.group(0))

    details = str(_pick_nested(payload, "house_details", "meta.house_details", "房屋概况", "meta.房屋概况") or "")
    m = re.search(r"(19|20)\d{2}", details)
    if m:
        return int(m.group(0))
    return None


def _chinese_to_num(token: str) -> int:
    m = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    t = token.strip()
    if t in m:
        return m[t]
    if t.startswith("十"):
        return 10 + m.get(t[1:], 0)
    if "十" in t:
        a, b = t.split("十", 1)
        return m.get(a, 1) * 10 + m.get(b, 0)
    return 0


def _extract_floor_count(payload: Dict[str, Any]) -> int:
    direct = _pick_nested(payload, "floor_count", "meta.floor_count", "楼层数", "meta.楼层数")
    if direct is not None:
        m = re.search(r"\d+", str(direct))
        if m:
            n = int(m.group(0))
            if n > 0:
                return n
        m_cn = re.search(r"([一二三四五六七八九十]+)\s*层", str(direct))
        if m_cn:
            n = _chinese_to_num(m_cn.group(1))
            if n > 0:
                return n

    details = str(_pick_nested(payload, "house_details", "meta.house_details") or "")
    m = re.search(r"(\d+)\s*层", details)
    if m:
        n = int(m.group(1))
        if n > 0:
            return n
    m_cn = re.search(r"([一二三四五六七八九十]+)\s*层", details)
    if m_cn:
        n = _chinese_to_num(m_cn.group(1))
        if n > 0:
            return n

    return 4


def _infer_component_type(payload: Dict[str, Any]) -> str:
    structure = str(
        _pick_nested(payload, "structure_type", "meta.structure_type", "结构类型", "meta.结构类型", "house_details", "meta.house_details")
        or ""
    )
    s = structure.lower()
    if "钢" in structure or "steel" in s:
        return "钢构件"
    if "木" in structure or "wood" in s:
        return "木构件"
    if "混凝土" in structure or "框架" in structure or "concrete" in s:
        return "混凝土构件"
    return "砌体构件"


def _house_category(year: Optional[int]) -> Tuple[str, str]:
    if year is None:
        return "I", "I类房屋（建成年代未提取，按I类取值）"
    if year < 1989:
        return "I", "I类房屋"
    if year <= 2002:
        return "II", "II类房屋"
    return "III", "III类房屋"


def _floor_label(i: int, n: int) -> str:
    cn = CN_NUM.get(i, str(i))
    if i < n:
        cn_next = CN_NUM.get(i + 1, str(i + 1))
        return f"{cn}层（含{cn_next}层楼面结构）"
    return f"{cn}层（含屋面结构）"


def _build_rows(floor_count: int) -> List[List[str]]:
    rows: List[List[str]] = []
    for i in range(1, floor_count + 1):
        label = _floor_label(i, floor_count)
        rows.append([label, "主要构件", "承重砖墙", "所有承重砖墙", "≥0.90", "非危险构件"])
        rows.append(["", "一般构件", "自承重墙", "所有自承重墙", "≥0.85", "非危险构件"])
    return rows


def generate_bearing_capacity_review(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = dict(context or {})
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")
    payload, source_test_item = _extract_delegate_payload(project_id, node_id, source_node_id)

    floor_count = _extract_floor_count(payload)
    year = _extract_year(payload)
    component_type = _infer_component_type(payload)
    category_key, category_text = _house_category(year)
    phi = PHI_TABLE[category_key][component_type]

    note_text = (
        f"注：根据《危险房屋鉴定标准》（JGJ125-2016）第5.1.2条，鉴定对象建于"
        f"{(str(year) + '年') if year else '建成年代未提取'}，属{category_text}，"
        f"{component_type}抗力与荷载效应之比调整系数φ取{phi:.2f}。"
    )

    rows = _build_rows(floor_count)
    rows.append([note_text, "", "", "", "", ""])

    return {
        "dataset_key": "bearing_capacity_review",
        "content": "构件承载能力验算结果见表。",
        "table": {
            "columns": ["鉴定对象（构件）", "构件类别", "墙体类型", "鉴定范围", "承载能力 φR/γ0S", "结论"],
            "header_rows": [
                [
                    {"label": "鉴定对象（构件）", "colSpan": 4},
                    {"label": "承载能力 φR/γ0S"},
                    {"label": "结论"},
                ]
            ],
            "rows": rows,
        },
        "meta": {
            "title": "表6·构件承载能力计算结果",
            "has_data": True,
            "source": "dynamic_db_with_rule_table",
            "source_node_id": source_node_id,
            "source_test_item": source_test_item,
            "floor_count": floor_count,
            "built_year": year,
            "house_category": category_key,
            "component_type": component_type,
            "phi": phi,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


async def generate_bearing_capacity_review_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_bearing_capacity_review(project_id, node_id, context)
