"""
Generate chapter: detailed inspection status.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import settings
from services.llm_gateway.gateway import LLMGateway

from .extract_utils import (
    extract_damage_alteration_items,
    extract_delegate_info,
    extract_settlement_inclination_text,
)


DEFAULT_ALTERATION_TEXT = "经现场检查，鉴定对象未见明显扩、接、加建情况。"
DEFAULT_SETTLEMENT_TEXT = "经现场检查，鉴定对象地基基础未见明显不均匀沉降，上部结构未见因地基变形引起的沉降裂缝，室内外地坪与主体间未见明显差异沉降，整体未见明显倾斜。"


def generate_detailed_inspection(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = dict(context or {})
    source_node_id = context.get("source_node_id") or context.get("sourceNodeId")
    scope_key = source_node_id if isinstance(source_node_id, str) and source_node_id.startswith("scope_") else None

    delegate_data = extract_delegate_info(
        project_id=project_id,
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=scope_key,
    )
    damage_rows = extract_damage_alteration_items(
        project_id=project_id,
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=scope_key,
    )
    settlement_text = extract_settlement_inclination_text(
        project_id=project_id,
        node_id=node_id,
        source_node_id=source_node_id,
        scope_key=scope_key,
    )

    if source_node_id and not str(source_node_id).startswith("scope_"):
        if not delegate_data:
            delegate_data = extract_delegate_info(
                project_id=project_id,
                node_id=node_id,
                source_node_id="scope_detailed_inspection",
                scope_key="scope_detailed_inspection",
            )
        if not damage_rows:
            damage_rows = extract_damage_alteration_items(
                project_id=project_id,
                node_id=node_id,
                source_node_id="scope_detailed_inspection",
                scope_key="scope_detailed_inspection",
            )
        if not settlement_text:
            settlement_text = extract_settlement_inclination_text(
                project_id=project_id,
                node_id=node_id,
                source_node_id="scope_detailed_inspection",
                scope_key="scope_detailed_inspection",
            )

    para1 = _compose_house_intro(delegate_data)

    explicit_alteration_text = _extract_explicit_alteration_text(delegate_data)
    alteration_candidates = _collect_alteration_candidates(damage_rows)
    para2 = _compose_alteration_paragraph(explicit_alteration_text, alteration_candidates)

    explicit_settlement_text = _extract_explicit_settlement_text(delegate_data)
    para3 = _compose_settlement_paragraph(explicit_settlement_text, settlement_text)

    sections = [
        {
            "section_number": "（一）",
            "section_title": "检查情况",
            "type": "text",
            "content": "\n".join([
                f"1.{para1}" if para1 else "",
                f"2.{para2}",
                f"3.{para3}",
            ]).strip(),
        },
        {
            "section_number": "",
            "section_title": "构件损伤及拆改检查情况",
            "type": "table",
            "table": {
                "columns": [
                    {"key": "inspection_location", "label": "检查位置"},
                    {"key": "status_description", "label": "现状描述"},
                    {"key": "photo_reference", "label": "照片"},
                ],
                "rows": damage_rows,
            },
        },
    ]

    return {
        "chapter_type": "detailed_inspection",
        "chapter_title": "检查和检测情况",
        "chapter_number": context.get("chapter_number", "五"),
        "sections": sections,
        "has_data": bool(delegate_data or damage_rows or settlement_text),
        "generation_metadata": {
            "skill_name": "detailed_inspection",
            "skill_version": "1.2.0",
            "generated_at": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "node_id": node_id,
            "source_node_id": source_node_id,
            "scope_key": scope_key,
            "alteration_explicit_text": explicit_alteration_text,
            "alteration_candidates": alteration_candidates,
        },
    }


async def generate_detailed_inspection_async(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result = generate_detailed_inspection(project_id, node_id, context)

    metadata = result.get("generation_metadata", {}) if isinstance(result.get("generation_metadata"), dict) else {}
    explicit_text = str(metadata.get("alteration_explicit_text") or "").strip()
    candidates = metadata.get("alteration_candidates") if isinstance(metadata.get("alteration_candidates"), list) else []

    if explicit_text or candidates:
        decision = await _judge_alteration_with_llm(explicit_text, candidates)
        para2 = _compose_alteration_by_decision(explicit_text, candidates, decision)
        _replace_second_paragraph(result, para2)

    return result


def _compose_house_intro(delegate_data: Dict[str, Any]) -> str:
    if not isinstance(delegate_data, dict) or not delegate_data:
        return "经现场检查，已完成鉴定对象房屋基本信息与结构体系核查。"

    meta = delegate_data.get("meta", {}) if isinstance(delegate_data.get("meta"), dict) else {}
    house_details = str(delegate_data.get("house_details") or "").strip()
    house_name = _first_non_empty(
        meta.get("house_name"),
        delegate_data.get("house_name"),
        delegate_data.get("鉴定对象"),
    )

    if house_details:
        return house_details
    if house_name:
        return f"鉴定对象为{house_name}，已完成房屋基本信息及结构体系核查。"
    return "经现场检查，已完成鉴定对象房屋基本信息与结构体系核查。"


def _extract_explicit_alteration_text(delegate_data: Dict[str, Any]) -> str:
    if not isinstance(delegate_data, dict):
        return ""
    meta = delegate_data.get("meta") if isinstance(delegate_data.get("meta"), dict) else {}

    for bucket in (delegate_data, meta):
        if not isinstance(bucket, dict):
            continue
        v = _first_non_empty(
            bucket.get("alteration_extension_text"),
            bucket.get("alteration_extension"),
            bucket.get("alteration_info"),
            bucket.get("modification_info"),
            bucket.get("expansion_info"),
            bucket.get("extension_info"),
            bucket.get("拆改加建情况"),
            bucket.get("拆改情况"),
            bucket.get("加建情况"),
            bucket.get("扩建情况"),
        )
        if v:
            return str(v).strip()
    return ""


def _collect_alteration_candidates(damage_rows: List[Dict[str, str]]) -> List[str]:
    candidates: List[str] = []
    for row in damage_rows or []:
        location = str(row.get("inspection_location") or "").strip()
        desc = str(row.get("status_description") or "").strip()
        text = f"{location}{desc}".strip()
        if text:
            candidates.append(text)
    return candidates


def _compose_alteration_paragraph(explicit_text: str, candidates: List[str]) -> str:
    if explicit_text:
        return _ensure_sentence_end(explicit_text)
    if candidates:
        sample = "；".join(candidates[:3]).strip("；")
        if sample:
            return f"经现场检查，鉴定对象存在以下拆改或加建情况：{sample}。"
    return DEFAULT_ALTERATION_TEXT


def _compose_alteration_by_decision(explicit_text: str, candidates: List[str], decision: Dict[str, Any]) -> str:
    has_issue = bool(decision.get("has_issue"))
    valid_items = decision.get("valid_items") if isinstance(decision.get("valid_items"), list) else []
    valid_items = [str(x).strip() for x in valid_items if str(x).strip()]

    if has_issue:
        if explicit_text and not valid_items:
            return _ensure_sentence_end(explicit_text)
        if valid_items:
            sample = "；".join(valid_items[:5]).strip("；")
            return f"经现场检查，鉴定对象存在以下拆改或加建情况：{sample}。"
        if explicit_text:
            return _ensure_sentence_end(explicit_text)

    return DEFAULT_ALTERATION_TEXT


async def _judge_alteration_with_llm(explicit_text: str, candidates: List[str]) -> Dict[str, Any]:
    payload = {
        "explicit_text": explicit_text,
        "candidates": candidates,
    }

    prompt = (
        "请判断下列文本是否属于‘拆改或加建’。\n"
        "判定规则：\n"
        "1) 仅当文本明确描述拆除、改造、改建、扩建、加建、洞口封堵、结构变更等，才算‘拆改或加建’。\n"
        "2) 仅描述渗水、起皮、脱落、裂缝、破损、锈蚀等病害，不算拆改或加建。\n"
        "3) 若没有任何拆改或加建信息，判定为无问题。\n"
        "请输出JSON：{\"has_issue\": bool, \"valid_items\": string[]}。\n"
        f"输入数据：{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        gateway = LLMGateway()
        resp = await gateway.chat_completion(
            provider=settings.llm_provider,
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "你是建筑检测报告语义判别助手。只输出JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = resp.get("content")
        if isinstance(content, str):
            parsed = json.loads(content)
        elif isinstance(content, dict):
            parsed = content
        else:
            parsed = {}

        if isinstance(parsed, dict):
            return {
                "has_issue": bool(parsed.get("has_issue")),
                "valid_items": parsed.get("valid_items") if isinstance(parsed.get("valid_items"), list) else [],
            }
    except Exception:
        pass

    return _rule_based_alteration_decision(explicit_text, candidates)


def _rule_based_alteration_decision(explicit_text: str, candidates: List[str]) -> Dict[str, Any]:
    positive_kw = ["拆", "改", "加建", "扩建", "改建", "改造", "新增", "封堵", "开洞", "拆除"]
    negative_kw = ["渗水", "起皮", "脱落", "裂缝", "破损", "锈蚀", "空鼓"]

    def is_positive(text: str) -> bool:
        t = str(text or "").strip()
        if not t:
            return False
        if any(k in t for k in positive_kw):
            return True
        if any(k in t for k in negative_kw):
            return False
        return False

    valid_items: List[str] = []
    if is_positive(explicit_text):
        valid_items.append(explicit_text)
    for c in candidates:
        if is_positive(c):
            valid_items.append(c)

    return {"has_issue": len(valid_items) > 0, "valid_items": valid_items}


def _extract_explicit_settlement_text(delegate_data: Dict[str, Any]) -> str:
    if not isinstance(delegate_data, dict):
        return ""
    meta = delegate_data.get("meta") if isinstance(delegate_data.get("meta"), dict) else {}

    for bucket in (delegate_data, meta):
        if not isinstance(bucket, dict):
            continue
        v = _first_non_empty(
            bucket.get("settlement_inclination_observation"),
            bucket.get("settlement_inclination"),
            bucket.get("settlement_observation"),
            bucket.get("inclination_observation"),
            bucket.get("沉降倾斜观测"),
            bucket.get("沉降及倾斜"),
            bucket.get("沉降情况"),
            bucket.get("倾斜情况"),
        )
        if v:
            return str(v).strip()
    return ""


def _compose_settlement_paragraph(explicit_settlement_text: str, settlement_text: str) -> str:
    if explicit_settlement_text:
        return _ensure_sentence_end(explicit_settlement_text)
    if settlement_text:
        return _ensure_sentence_end(settlement_text)
    return DEFAULT_SETTLEMENT_TEXT


def _replace_second_paragraph(result: Dict[str, Any], paragraph_text: str) -> None:
    sections = result.get("sections") if isinstance(result.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict) or section.get("type") != "text":
            continue
        content = str(section.get("content") or "")
        lines = content.split("\n")
        new_lines: List[str] = []
        replaced = False
        for line in lines:
            if line.strip().startswith("2."):
                new_lines.append(f"2.{paragraph_text}")
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.insert(1, f"2.{paragraph_text}")
        section["content"] = "\n".join(new_lines).strip()
        break


def _ensure_sentence_end(text: str) -> str:
    t = str(text or "").strip()
    if not t:
        return ""
    if t.endswith(("。", "！", "？", ".", "!", "?")):
        return t
    return f"{t}。"


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        t = str(value).strip()
        if t:
            return t
    return ""
