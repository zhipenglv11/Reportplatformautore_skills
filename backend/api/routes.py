from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List
import json
import uuid

from api import collection_routes
from config import settings
from models.db import insert_run_log
from services.llm_gateway.gateway import LLMGateway
from services.skills.chapter_generation_skill import ChapterGenerationSkill

router = APIRouter()

# 挂载数据采集相关的路由
router.include_router(collection_routes.router)


class GenerateReportRequest(BaseModel):
    project_id: str
    chapter_config: dict
    project_context: dict


@router.post("/report/generate")
async def generate_report(request: GenerateReportRequest):
    """生成报告 - Phase 0版本（串行调用）"""
    report_id = str(uuid.uuid4())
    run_id = report_id
    try:
        skill = ChapterGenerationSkill()
        chapter = skill.execute(
            project_id=request.project_id,
            chapter_config=request.chapter_config or {},
        )

        blocks: List[Dict[str, Any]] = chapter.blocks or []
        dataset_key = request.chapter_config.get("dataset_key")
        use_llm = bool(request.chapter_config.get("use_llm"))
        if dataset_key == "concrete_strength_description" and use_llm:
            text_block = next((block for block in blocks if block.get("type") == "text"), None)
            facts = (text_block or {}).get("facts") or {}
            if text_block and facts:
                llm_gateway = LLMGateway()
                prompt = (
                    "请根据以下事实生成一段工程报告描述文字，"
                    "不得引入未提供的信息，不得进行计算或推断：\n"
                    f"{json.dumps(facts, ensure_ascii=False)}"
                )
                llm_response = await llm_gateway.chat_completion(
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": "工程报告文本生成助手，只输出中文描述文本。"},
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
            if not isinstance(columns, list) or not isinstance(rows, list):
                raise ValueError("chapter_generation_invalid_table_shape")
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
                    "template_style": chapter.template_style,
                    "reference_spec": chapter.reference_spec,
                    "rows": len(table_blocks[0].get("rows") or []) if table_blocks else 0,
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
                    "chapter_id": chapter.chapter_id,
                    "title": chapter.title,
                    "chapter_content": {
                        "template_style": chapter.template_style,
                        "reference_spec_type": chapter.reference_spec_type,
                        "reference_spec": chapter.reference_spec,
                        "blocks": blocks,
                        "summary": chapter.summary,
                    },
                    "evidence_refs": chapter.evidence_refs,
                }
            ],
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
    """查询运行状态和日志"""
    return {
        "run_id": run_id,
        "status": "RUNNING",
        "skill_steps": [],
        "llm_usage": [],
    }
