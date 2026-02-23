from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List
import json
import uuid

from api import collection_routes
from config import settings
from models.db import insert_run_log
from services.llm_gateway.gateway import LLMGateway

# 瀵煎叆鏂扮殑澹版槑寮忔妧鑳?
from skills_library.generation.inspection.material_strength.subskills.concrete_strength.impl.parse import parse_concrete_strength
from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
from skills_library.generation.inspection.material_strength.subskills.mortar_strength.impl.parse import parse_mortar_strength
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

router = APIRouter()

# 鎸傝浇鏁版嵁閲囬泦鐩稿叧鐨勮矾鐢?
router.include_router(collection_routes.router)


class GenerateReportRequest(BaseModel):
    project_id: str
    chapter_config: dict
    project_context: dict


@router.post("/report/generate")
async def generate_report(request: GenerateReportRequest):
    """鐢熸垚鎶ュ憡 - 浣跨敤鏂扮殑 Declarative Skills 绯荤粺"""
    report_id = str(uuid.uuid4())
    run_id = report_id
    
    # 娣诲姞璋冭瘯鏃ュ織
    import sys
    
    try:
        dataset_key = request.chapter_config.get("dataset_key")
        project_id = request.project_id
        node_id = request.chapter_config.get("node_id") or request.chapter_config.get("chapter_id") or "chapter"
        context = request.chapter_config.get("context") or {}
        if not isinstance(context, dict):
            context = {}

        # Backward/forward compatible source selector for dynamic data binding.
        source_node_id = (
            request.chapter_config.get("sourceNodeId")
            or request.chapter_config.get("source_node_id")
        )
        if source_node_id:
            context.setdefault("source_node_id", source_node_id)
            context.setdefault("sourceNodeId", source_node_id)
        
        print(f"[DEBUG] generate_report called:", file=sys.stderr)
        print(f"  - dataset_key: {dataset_key}", file=sys.stderr)
        print(f"  - project_id: {project_id}", file=sys.stderr)
        print(f"  - node_id: {node_id}", file=sys.stderr)
        
        # 鏍规嵁 dataset_key 璺敱鍒板搴旂殑鎶€鑳?
        skill_result = None
        
        if dataset_key in ["concrete_strength", "concrete_rebound_tests", "concrete_strength_comprehensive"]:
            print(f"[DEBUG] Calling parse_concrete_strength", file=sys.stderr)
            skill_result = await parse_concrete_strength(project_id, node_id, context)
        elif dataset_key == "brick_strength":
            print(f"[DEBUG] Calling parse_brick_strength", file=sys.stderr)
            skill_result = await parse_brick_strength(project_id, node_id, context)
        elif dataset_key == "mortar_strength":
            print(f"[DEBUG] Calling parse_mortar_strength", file=sys.stderr)
            skill_result = await parse_mortar_strength(project_id, node_id, context)
        elif dataset_key == "inspection_content_and_methods":
            # This chapter should prefer real dynamic data and avoid silent static fallback.
            context.setdefault("use_dynamic_data", True)
            context.setdefault("allow_static_fallback", False)
            print(f"[DEBUG] Calling generate_inspection_content_and_methods_async", file=sys.stderr)
            skill_result = await generate_inspection_content_and_methods_async(project_id, node_id, context)
        elif dataset_key == "inspection_basis":
            print(f"[DEBUG] Calling generate_inspection_basis_async", file=sys.stderr)
            skill_result = await generate_inspection_basis_async(project_id, node_id, context)
        elif dataset_key == "detailed_inspection":
            context.setdefault("use_dynamic_data", True)
            print(f"[DEBUG] Calling generate_detailed_inspection_async", file=sys.stderr)
            skill_result = await generate_detailed_inspection_async(project_id, node_id, context)
        elif dataset_key == "basic_situation":
            context.setdefault("use_dynamic_data", True)
            print(f"[DEBUG] Calling generate_basic_situation_async", file=sys.stderr)
            skill_result = await generate_basic_situation_async(project_id, node_id, context)
        elif dataset_key == "house_overview":
            context.setdefault("use_dynamic_data", True)
            print(f"[DEBUG] Calling generate_house_overview_async", file=sys.stderr)
            skill_result = await generate_house_overview_async(project_id, node_id, context)
        elif dataset_key == "load_calc_params":
            context.setdefault("use_dynamic_data", True)
            print(f"[DEBUG] Calling generate_load_calc_params_async", file=sys.stderr)
            skill_result = await generate_load_calc_params_async(project_id, node_id, context)
        elif dataset_key == "bearing_capacity_review":
            context.setdefault("use_dynamic_data", True)
            print(f"[DEBUG] Calling generate_bearing_capacity_review_async", file=sys.stderr)
            skill_result = await generate_bearing_capacity_review_async(project_id, node_id, context)
        elif dataset_key == "analysis_explanation":
            print(f"[DEBUG] Calling generate_analysis_explanation_async", file=sys.stderr)
            skill_result = await generate_analysis_explanation_async(project_id, node_id, context)
        elif dataset_key == "opinion_and_suggestions":
            print(f"[DEBUG] Calling generate_opinion_and_suggestions_async", file=sys.stderr)
            skill_result = await generate_opinion_and_suggestions_async(project_id, node_id, context)
        else:
            raise ValueError(f"涓嶆敮鎸佺殑 dataset_key: {dataset_key}")
        
        print(f"[DEBUG] Skill result keys: {skill_result.keys()}", file=sys.stderr)
        print(f"[DEBUG] Has content: {bool(skill_result.get('content'))}", file=sys.stderr)
        print(f"[DEBUG] Has table: {bool(skill_result.get('table'))}", file=sys.stderr)
        
        # 灏嗘柊鏍煎紡杞崲涓烘棫鏍煎紡锛堜繚鎸佸墠绔吋瀹癸級
        blocks: List[Dict[str, Any]] = []

        if dataset_key in ["inspection_content_and_methods", "detailed_inspection", "analysis_explanation", "opinion_and_suggestions"]:
            for section in skill_result.get("sections", []):
                section_number = section.get("section_number", "")
                section_title = section.get("section_title", "")
                if section.get("type") == "text":
                    section_header = f"{section_number} {section_title}".strip()
                    section_body = section.get("content", "")
                    text_content = f"{section_header}\n{section_body}".strip()
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
                blocks.append(
                    {
                        "type": "text",
                        "text": skill_result["content"],
                        "facts": skill_result.get("meta", {}),
                    }
                )
        elif dataset_key == "basic_situation":
            items = skill_result.get("items") or []
            if isinstance(items, list) and items:
                blocks.append(
                    {
                        "type": "kv_list",
                        "title": "基本情况",
                        "items": items,
                    }
                )
            if not blocks:
                blocks.append(
                    {
                        "type": "note",
                        "text": "??????????????????????????????",
                    }
                )
        elif dataset_key == "house_overview":
            if skill_result.get("content"):
                blocks.append(
                    {
                        "type": "text",
                        "text": skill_result["content"],
                        "facts": skill_result.get("meta", {}).get("facts", {}),
                    }
                )
            if not blocks:
                blocks.append(
                    {
                        "type": "note",
                        "text": "未找到房屋概况相关数据。请确保已上传委托信息并完成信息抽取。",
                    }
                )
        else:
            # 鏃х殑鏉愭枡寮哄害绫昏緭鍑烘牸寮?
            # 妫€鏌ユ槸鍚︽湁鏁版嵁
            has_data = skill_result.get("meta", {}).get("has_data", True)
            print(f"[DEBUG] has_data: {has_data}", file=sys.stderr)
            if not has_data:
                # 如果没有数据，返回提示信息
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
                note_block = {
                    "type": "note",
                    "text": f"{note_text}。请确保已上传相关文件并完成信息抽取。"
                }
                print(f"[DEBUG] Adding note block: {note_block}", file=sys.stderr)
                blocks.append(note_block)
            else:
                # 娣诲姞鏂囨湰鍧?
                if skill_result.get("content"):
                    blocks.append({
                        "type": "text",
                        "text": skill_result["content"],
                        "facts": skill_result.get("meta", {})
                    })
                
                # 娣诲姞琛ㄦ牸鍧?
                table = skill_result.get("table", {})
                if table.get("columns") and table.get("rows"):
                    # 灏嗘柊鏍煎紡鐨?columns 杞崲涓烘棫鏍煎紡
                    columns = [{"key": col, "label": col} for col in table["columns"]]
                    
                    # 灏嗚鏁版嵁杞崲涓哄瓧鍏告牸寮?
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
                        "rows": rows
                    })
        
        print(f"[DEBUG] Generated {len(blocks)} blocks", file=sys.stderr)
        if len(blocks) > 0:
            print(f"[DEBUG] First block: {blocks[0]}", file=sys.stderr)

        # LLM polish
        use_llm = bool(request.chapter_config.get("use_llm")) or dataset_key == "house_overview"
        if use_llm:
            text_block = next((block for block in blocks if block.get("type") == "text"), None)
            facts = (text_block or {}).get("facts") or {}
            if text_block and facts:
                llm_gateway = LLMGateway()
                if dataset_key == "house_overview":
                    cfg_context = request.chapter_config.get("context") if isinstance(request.chapter_config.get("context"), dict) else {}
                    custom_prompt = cfg_context.get("house_overview_polish_prompt") if isinstance(cfg_context, dict) else None
                    prompt = custom_prompt or (
                        "请将以下‘房屋概况’事实润色为工程鉴定报告段落："
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
        if not blocks:
            raise ValueError("chapter_generation_missing_blocks")
        table_blocks = [block for block in blocks if block.get("type") == "table"]
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

        insert_run_log(
            {
                "run_id": run_id,
                "project_id": request.project_id,
                "node_id": request.chapter_config.get("node_id"),
                "record_id": None,
                "status": "SUCCESS",
                "stage": "chapter_generation",
                "prompt_version": "v1",
                "schema_version": "v1",
                "input_file_hashes": {},
                "skill_steps": {
                    "skill_type": "declarative_skill",
                    "dataset_key": dataset_key,
                    "rows": len(table_blocks[0].get("rows", [])) if table_blocks else 0,
                    "block_count": len(blocks),
                },
                "llm_usage": {},
                "total_cost": 0,
                "error_message": None,
            }
        )

        return {
            "report_id": report_id,
            "chapters": [
                {
                    "chapter_id": node_id,
                    "title": request.chapter_config.get("title", ""),
                    "chapter_content": {
                        "blocks": blocks
                    },
                    "summary": skill_result.get("meta", {}),
                    "evidence_refs": skill_result.get("meta", {}).get("evidence_refs", [])
                }
            ]
        }
    except Exception as exc:
        insert_run_log(
            {
                "run_id": run_id,
                "project_id": request.project_id,
                "node_id": request.chapter_config.get("node_id"),
                "record_id": None,
                "status": "FAILED",
                "stage": "chapter_generation",
                "prompt_version": "v1",
                "schema_version": "v1",
                "input_file_hashes": {},
                "skill_steps": {},
                "llm_usage": {},
                "total_cost": 0,
                "error_message": str(exc),
            }
        )
        raise


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    """鏌ヨ杩愯鐘舵€佸拰鏃ュ織"""
    return {
        "run_id": run_id,
        "status": "RUNNING",
        "skill_steps": [],
        "llm_usage": [],
    }
