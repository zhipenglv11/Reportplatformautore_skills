# -*- coding: utf-8 -*-
"""
报告生成核心：根据 dataset_key 调度对应技能，并将结果归一化为 blocks。
"""

import json
import sys
from typing import Any, Dict, List

from config import settings
from core.llm.gateway import LLMGateway

from skills_library.generation.inspection.material_strength.subskills.concrete_strength.impl.parse import (
    parse_concrete_strength,
)
from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import (
    parse_brick_strength,
)
from skills_library.generation.inspection.material_strength.subskills.mortar_strength.impl.parse import (
    parse_mortar_strength,
)
from skills_library.generation.inspection.inspection_content_and_methods.impl.generate import (
    generate_inspection_content_and_methods_async,
)
from skills_library.generation.inspection.inspection_basis.impl.generate import (
    generate_inspection_basis_async,
)
from skills_library.generation.inspection.detailed_inspection.impl.generate import (
    generate_detailed_inspection_async,
)
from skills_library.generation.inspection.basic_situation.impl.generate import (
    generate_basic_situation_async,
)
from skills_library.generation.inspection.house_overview.impl.generate import (
    generate_house_overview_async,
)
from skills_library.generation.inspection.load_calc_params.impl.generate import (
    generate_load_calc_params_async,
)
from skills_library.generation.inspection.bearing_capacity_review.impl.generate import (
    generate_bearing_capacity_review_async,
)
from skills_library.generation.inspection.analysis_explanation.impl.generate import (
    generate_analysis_explanation_async,
)
from skills_library.generation.inspection.opinion_and_suggestions.impl.generate import (
    generate_opinion_and_suggestions_async,
)


async def dispatch_skill(
    dataset_key: str,
    project_id: str,
    node_id: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """根据 dataset_key 调度到对应的技能并返回原始 skill_result。"""

    if dataset_key in [
        "concrete_strength",
        "concrete_rebound_tests",
        "concrete_strength_comprehensive",
    ]:
        return await parse_concrete_strength(project_id, node_id, context)
    if dataset_key == "brick_strength":
        return await parse_brick_strength(project_id, node_id, context)
    if dataset_key == "mortar_strength":
        return await parse_mortar_strength(project_id, node_id, context)
    if dataset_key == "inspection_content_and_methods":
        context.setdefault("use_dynamic_data", True)
        context.setdefault("allow_static_fallback", False)
        return await generate_inspection_content_and_methods_async(project_id, node_id, context)
    if dataset_key == "inspection_basis":
        return await generate_inspection_basis_async(project_id, node_id, context)
    if dataset_key == "detailed_inspection":
        context.setdefault("use_dynamic_data", True)
        return await generate_detailed_inspection_async(project_id, node_id, context)
    if dataset_key == "basic_situation":
        context.setdefault("use_dynamic_data", True)
        return await generate_basic_situation_async(project_id, node_id, context)
    if dataset_key == "house_overview":
        context.setdefault("use_dynamic_data", True)
        return await generate_house_overview_async(project_id, node_id, context)
    if dataset_key == "load_calc_params":
        context.setdefault("use_dynamic_data", True)
        return await generate_load_calc_params_async(project_id, node_id, context)
    if dataset_key == "bearing_capacity_review":
        context.setdefault("use_dynamic_data", True)
        return await generate_bearing_capacity_review_async(project_id, node_id, context)
    if dataset_key == "analysis_explanation":
        return await generate_analysis_explanation_async(project_id, node_id, context)
    if dataset_key == "opinion_and_suggestions":
        return await generate_opinion_and_suggestions_async(project_id, node_id, context)

    raise ValueError(f"不支持的 dataset_key: {dataset_key}")


def normalize_blocks(
    dataset_key: str,
    skill_result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """将各技能的输出格式归一化为前端所需的 blocks 列表。"""

    blocks: List[Dict[str, Any]] = []

    section_based_keys = {
        "inspection_content_and_methods",
        "detailed_inspection",
        "analysis_explanation",
        "opinion_and_suggestions",
    }

    if dataset_key in section_based_keys:
        for section in skill_result.get("sections", []):
            section_number = section.get("section_number", "")
            section_title = section.get("section_title", "")
            if section.get("type") == "text":
                header = f"{section_number} {section_title}".strip()
                body = section.get("content", "")
                text_content = f"{header}\n{body}".strip()
                if text_content:
                    blocks.append({
                        "type": "text",
                        "text": text_content,
                        "facts": skill_result.get("generation_metadata", {}),
                    })
            elif section.get("type") == "table":
                table = section.get("table", {})
                raw_columns = table.get("columns") or []
                columns = raw_columns
                if raw_columns and not isinstance(raw_columns[0], dict):
                    columns = [{"key": col, "label": col} for col in raw_columns]
                rows = table.get("rows") or []
                if rows and isinstance(rows[0], list):
                    normalized_rows = []
                    for row in rows:
                        row_dict = {}
                        for idx, col in enumerate(raw_columns):
                            row_dict[col] = row[idx] if idx < len(row) else ""
                        normalized_rows.append(row_dict)
                    rows = normalized_rows
                blocks.append({
                    "type": "table",
                    "table_id": skill_result.get("chapter_type"),
                    "title": f"{section_number} {section_title}".strip(),
                    "columns": columns,
                    "header_rows": table.get("header_rows") or [],
                    "body_rows": table.get("body_rows") or [],
                    "rows": rows,
                })

    elif dataset_key == "inspection_basis":
        if skill_result.get("content"):
            blocks.append({
                "type": "text",
                "text": skill_result["content"],
                "facts": skill_result.get("meta", {}),
            })

    elif dataset_key == "basic_situation":
        items = skill_result.get("items") or []
        if isinstance(items, list) and items:
            blocks.append({
                "type": "kv_list",
                "title": "基本情况",
                "items": items,
            })
        if not blocks:
            blocks.append({
                "type": "note",
                "text": "未找到基本情况相关数据。请确保已上传委托信息并完成信息抽取。",
            })

    elif dataset_key == "house_overview":
        if skill_result.get("content"):
            blocks.append({
                "type": "text",
                "text": skill_result["content"],
                "facts": skill_result.get("meta", {}).get("facts", {}),
            })
        if not blocks:
            blocks.append({
                "type": "note",
                "text": "未找到房屋概况相关数据。请确保已上传委托信息并完成信息抽取。",
            })

    else:
        has_data = skill_result.get("meta", {}).get("has_data", True)
        if not has_data:
            meta = skill_result.get("meta", {}) if isinstance(skill_result.get("meta"), dict) else {}
            material_type_raw = meta.get("material_type", "数据")
            material_type_cn_map = {
                "mortar": "砂浆",
                "concrete": "混凝土",
                "brick": "砖",
                "steel": "钢材",
            }
            material_type = material_type_cn_map.get(material_type_raw, material_type_raw)
            warnings = meta.get("warnings") if isinstance(meta.get("warnings"), list) else []
            warning_text = next((str(item).strip() for item in warnings if str(item).strip()), "")
            note_text = warning_text or f"未找到{material_type}相关的检测数据"
            blocks.append({
                "type": "note",
                "text": f"{note_text}。请确保已上传相关文件并完成信息抽取。",
            })
        else:
            if skill_result.get("content"):
                blocks.append({
                    "type": "text",
                    "text": skill_result["content"],
                    "facts": skill_result.get("meta", {}),
                })
            table = skill_result.get("table", {})
            if table.get("columns") and table.get("rows"):
                columns = [{"key": col, "label": col} for col in table["columns"]]
                rows = []
                for row in table["rows"]:
                    row_dict = {}
                    for idx, col in enumerate(table["columns"]):
                        row_dict[col] = row[idx] if idx < len(row) else ""
                    rows.append(row_dict)
                blocks.append({
                    "type": "table",
                    "table_id": skill_result.get("dataset_key"),
                    "title": skill_result.get("meta", {}).get("title", ""),
                    "columns": columns,
                    "header_rows": table.get("header_rows") or [],
                    "body_rows": table.get("body_rows") or [],
                    "rows": rows,
                })

    return blocks


async def maybe_llm_polish(
    blocks: List[Dict[str, Any]],
    dataset_key: str,
    chapter_config: Dict[str, Any],
) -> None:
    """可选的 LLM 润色（原地修改 blocks 中的 text block）。"""

    use_llm = bool(chapter_config.get("use_llm")) or dataset_key == "house_overview"
    if not use_llm:
        return

    text_block = next((b for b in blocks if b.get("type") == "text"), None)
    facts = (text_block or {}).get("facts") or {}
    if not text_block or not facts:
        return

    llm_gateway = LLMGateway()

    if dataset_key == "house_overview":
        cfg_context = chapter_config.get("context") if isinstance(chapter_config.get("context"), dict) else {}
        custom_prompt = cfg_context.get("house_overview_polish_prompt") if isinstance(cfg_context, dict) else None
        prompt = custom_prompt or (
            "请将以下'房屋概况'事实润色为工程鉴定报告段落："
            "仅基于事实，不编造；语言正式、连贯；输出单段中文；保留数字、单位和附件编号。"
        )
        prompt = f"{prompt}\n\n事实数据：\n{json.dumps(facts, ensure_ascii=False)}"
        system_prompt = "你是建筑工程鉴定报告写作助手。"
    else:
        prompt = (
            "请根据以下事实生成一段工程报告描述文字，"
            "不得引入未提供的信息，不得进行计算或推断：\n"
            f"{json.dumps(facts, ensure_ascii=False)}"
        )
        system_prompt = "工程报告文本生成助手，只输出中文描述文本。"

    llm_response = await llm_gateway.chat_completion(
        provider=settings.llm_provider,
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    llm_text = llm_response.get("content")
    if isinstance(llm_text, str) and llm_text.strip():
        text_block["text"] = llm_text.strip()


def validate_table_blocks(blocks: List[Dict[str, Any]]) -> None:
    """校验 blocks 中 table 类型的结构完整性。"""

    table_blocks = [b for b in blocks if b.get("type") == "table"]
    for block in table_blocks:
        columns = block.get("columns") or []
        rows = block.get("rows") or []
        body_rows = block.get("body_rows") or []
        if not isinstance(columns, list) or not isinstance(rows, list):
            raise ValueError("chapter_generation_invalid_table_shape")
        if body_rows:
            if not isinstance(body_rows, list):
                raise ValueError("chapter_generation_invalid_table_body_rows")
        else:
            column_keys = [col.get("key") for col in columns if isinstance(col, dict)]
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("chapter_generation_invalid_table_row")
                missing_keys = [key for key in column_keys if key not in row]
                if missing_keys:
                    raise ValueError(f"chapter_generation_missing_columns:{','.join(missing_keys)}")
