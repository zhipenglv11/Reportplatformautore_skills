"""Generate chapter: 检测鉴定依据（优先数据库动态读取）"""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text


REPORT_TYPE_TO_STANDARDS: Dict[str, List[Dict[str, str]]] = {
    "民标安全性": [
        {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
        {"name": "民用建筑可靠性鉴定标准", "code": "GB50292-2015"},
    ],
    "危险房屋鉴定": [
        {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
    ],
    "抗震鉴定": [
        {"name": "建筑抗震鉴定标准", "code": "GB50023-2009"},
    ],
    "主体结构施工质量鉴定": [
        {"name": "混凝土结构工程施工质量验收规范", "code": "GB50204-2015"},
        {"name": "砌体结构工程施工质量验收规范", "code": "GB50203-2011"},
    ],
}

DEFAULT_STANDARDS: List[Dict[str, str]] = [
    {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
]

CODE_TO_NAME: Dict[str, str] = {
    "JGJ125-2016": "危险房屋鉴定标准",
    "GB50292-2015": "民用建筑可靠性鉴定标准",
    "JGJ/T23-2011": "回弹法检测混凝土抗压强度技术规程",
    "GB50023-2009": "建筑抗震鉴定标准",
    "GB50204-2015": "混凝土结构工程施工质量验收规范",
    "GB50203-2011": "砌体结构工程施工质量验收规范",
}

NAME_ALIAS_TO_STANDARD: Dict[str, Dict[str, str]] = {
    "危房": {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
    "危险房屋": {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
    "危险性鉴定": {"name": "危险房屋鉴定标准", "code": "JGJ125-2016"},
    "民用建筑可靠性": {"name": "民用建筑可靠性鉴定标准", "code": "GB50292-2015"},
    "回弹法": {"name": "回弹法检测混凝土抗压强度技术规程", "code": "JGJ/T23-2011"},
}

SCOPE_TEST_ITEM_KEYWORDS: Dict[str, List[str]] = {
    "scope_inspection_basis": ["delegate_info_recognition", "delegate", "inspection_basis"],
}


def _normalize_report_type(value: Optional[str]) -> str:
    text_value = (value or "").strip()
    aliases = {
        "民用建筑可靠性": "民标安全性",
        "民用可靠性": "民标安全性",
        "民标": "民标安全性",
    }
    return aliases.get(text_value, text_value)


def _parse_json_field(field_value: Any) -> Dict[str, Any]:
    if not field_value:
        return {}
    if isinstance(field_value, dict):
        return field_value
    if isinstance(field_value, str):
        try:
            parsed = json.loads(field_value)
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


def _normalize_code(code: str) -> str:
    text_value = (code or "").upper().strip()
    text_value = text_value.replace("（", "(").replace("）", ")")
    text_value = re.sub(r"\s+", "", text_value)

    # JGJ/T23-2011, JGJ125-2016, GB50292-2015...
    match = re.search(r"(JGJ/T\d+-\d+|JGJ\d+-\d+|GB/T\d+-\d+|GB\d+-\d+|DB[0-9A-Z./-]*\d+-\d+)", text_value)
    if match:
        return match.group(1)
    return text_value


def _is_standard_code(code: str) -> bool:
    return bool(re.search(r"^(JGJ/T|JGJ|GB/T|GB|DB).*\d+-\d+$", (code or "").upper()))


def _parse_reference_spec(reference_spec: Optional[str]) -> List[Dict[str, str]]:
    if not reference_spec:
        return []
    raw = reference_spec.strip()
    if not raw:
        return []

    standards: List[Dict[str, str]] = []
    for part in re.split(r"[;；\n]+", raw):
        p = part.strip()
        if not p:
            continue

        # 形如《规范名》（CODE）
        name = ""
        code = ""
        m_name = re.search(r"《([^》]+)》", p)
        m_code = re.search(r"[（(]([^()（）]+)[)）]", p)
        if m_name:
            name = m_name.group(1).strip()
        if m_code:
            code = _normalize_code(m_code.group(1))

        if not code:
            maybe_code = _normalize_code(p)
            code = maybe_code if _is_standard_code(maybe_code) else ""
        if not name:
            name = CODE_TO_NAME.get(code, "检测鉴定依据")

        if code:
            standards.append({"name": name, "code": code})

    return _dedupe_standards(standards)


def _extract_candidates_from_result(data: Dict[str, Any]) -> List[str]:
    if not isinstance(data, dict):
        return []
    meta = data.get("meta", {}) if isinstance(data.get("meta", {}), dict) else {}

    keys = [
        "inspection_basis", "inspection_standard", "reference_spec", "basis",
        "检测依据", "鉴定依据", "规范依据", "检测鉴定依据",
    ]

    candidates: List[str] = []
    for key in keys:
        for bucket in (meta, data):
            value = bucket.get(key)
            if value is None:
                continue
            if isinstance(value, list):
                candidates.extend(str(v).strip() for v in value if str(v).strip())
            else:
                s = str(value).strip()
                if s:
                    candidates.append(s)

    # inspection_reason 等可能是简称
    reason = str(meta.get("inspection_reason") or data.get("inspection_reason") or "").strip()
    if reason:
        candidates.append(reason)

    return candidates


def _candidate_to_standard(candidate: str) -> List[Dict[str, str]]:
    text_value = (candidate or "").strip()
    if not text_value:
        return []

    # 先尝试按 reference_spec 格式解析
    parsed = _parse_reference_spec(text_value)
    if parsed and any(_is_standard_code(item.get("code", "")) for item in parsed):
        out: List[Dict[str, str]] = []
        for item in parsed:
            code = _normalize_code(item.get("code", ""))
            if not _is_standard_code(code):
                continue
            if not code:
                continue
            name = item.get("name") or CODE_TO_NAME.get(code, "检测鉴定依据")
            out.append({"name": name, "code": code})
        if out:
            return _dedupe_standards(out)

    # 再按别名关键词匹配
    lowered = text_value.lower()
    for keyword, standard in NAME_ALIAS_TO_STANDARD.items():
        if keyword.lower() in lowered:
            return [standard]

    # 兜底尝试从文本中抽 code
    code = _normalize_code(text_value)
    if code and re.search(r"\d+-\d+", code):
        return [{"name": CODE_TO_NAME.get(code, "检测鉴定依据"), "code": code}]

    return []


def _dedupe_standards(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    dedup: Dict[Tuple[str, str], Dict[str, str]] = {}
    for item in items:
        name = (item.get("name") or "").strip()
        code = _normalize_code(item.get("code") or "")
        if not code and not name:
            continue
        if not name and code:
            name = CODE_TO_NAME.get(code, "检测鉴定依据")
        key = (name, code)
        if key not in dedup:
            dedup[key] = {"name": name, "code": code}
    return list(dedup.values())


def _extract_standards_from_db(
    project_id: str,
    node_id: str,
    source_node_id: Optional[str],
) -> List[Dict[str, str]]:
    from models.db import get_engine

    effective_node_id, effective_scope = _resolve_filters(
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None,
    )

    engine = get_engine()
    standards: List[Dict[str, str]] = []

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
            candidates = _extract_candidates_from_result(data)
            for candidate in candidates:
                standards.extend(_candidate_to_standard(candidate))

    return _dedupe_standards(standards)


def generate_inspection_basis(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = context or {}

    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")

    # 1) 前端显式选择 > 2) 数据库动态读取 > 3) 报告类型默认映射
    explicit_standards = _parse_reference_spec(context.get("reference_spec") or context.get("referenceSpec"))
    db_standards = _extract_standards_from_db(project_id, node_id, source_node_id)

    report_type = _normalize_report_type(context.get("report_type") or context.get("reportType"))
    report_defaults = list(REPORT_TYPE_TO_STANDARDS.get(report_type, DEFAULT_STANDARDS))

    standards = explicit_standards or db_standards or report_defaults
    standards = _dedupe_standards(standards)

    lines = [f"{idx}、《{item['name']}》（{item['code']}）" for idx, item in enumerate(standards, start=1)]
    content = "\n".join(lines)

    return {
        "dataset_key": "inspection_basis",
        "content": content,
        "table": {"columns": [], "rows": []},
        "meta": {
            "title": "检测鉴定依据",
            "report_type": report_type,
            "standards": standards,
            "generated_at": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "node_id": node_id,
            "source_node_id": source_node_id,
            "data_source": "reference_spec" if explicit_standards else ("database" if db_standards else "report_type_default"),
        },
    }


async def generate_inspection_basis_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return generate_inspection_basis(project_id, node_id, context)
