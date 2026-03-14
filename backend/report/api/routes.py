# -*- coding: utf-8 -*-
"""报告生成 API 路由"""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from core.models.db import insert_run_log
from report.services.report_generator import (
    dispatch_skill,
    normalize_blocks,
    maybe_llm_polish,
    validate_table_blocks,
)
from report.services.report_demo import is_report_demo_enabled

router = APIRouter()


class GenerateReportRequest(BaseModel):
    project_id: str
    chapter_config: dict
    project_context: dict


def _record_run_log(payload: Dict[str, Any]) -> None:
    try:
        insert_run_log(payload)
    except Exception:
        if not is_report_demo_enabled():
            raise


@router.post("/report/generate")
async def generate_report(request: GenerateReportRequest):
    """生成报告章节"""
    report_id = str(uuid.uuid4())
    run_id = report_id

    try:
        dataset_key = request.chapter_config.get("dataset_key")
        project_id = request.project_id
        node_id = (
            request.chapter_config.get("node_id")
            or request.chapter_config.get("chapter_id")
            or "chapter"
        )
        context = request.chapter_config.get("context") or {}
        if not isinstance(context, dict):
            context = {}

        source_node_id = (
            request.chapter_config.get("sourceNodeId")
            or request.chapter_config.get("source_node_id")
        )
        if source_node_id:
            context.setdefault("source_node_id", source_node_id)
            context.setdefault("sourceNodeId", source_node_id)

        skill_result = await dispatch_skill(dataset_key, project_id, node_id, context)
        skill_meta = skill_result.get("meta", {}) if isinstance(skill_result.get("meta"), dict) else {}

        blocks = normalize_blocks(dataset_key, skill_result)

        await maybe_llm_polish(blocks, dataset_key, request.chapter_config)

        if not blocks:
            raise ValueError("chapter_generation_missing_blocks")

        validate_table_blocks(blocks)

        table_blocks = [b for b in blocks if b.get("type") == "table"]
        _record_run_log({
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
                "skill_type": "report_demo_fixture" if skill_meta.get("demo_mode") else "generation_skill",
                "dataset_key": dataset_key,
                "rows": len(table_blocks[0].get("rows", [])) if table_blocks else 0,
                "block_count": len(blocks),
                "demo_mode": bool(skill_meta.get("demo_mode")),
                "demo_profile": skill_meta.get("demo_profile"),
            },
            "llm_usage": {},
            "total_cost": 0,
            "error_message": None,
        })

        return {
            "report_id": report_id,
            "chapters": [
                {
                    "chapter_id": node_id,
                    "title": request.chapter_config.get("title", ""),
                    "chapter_content": {"blocks": blocks},
                    "summary": skill_result.get("meta", {}),
                    "evidence_refs": skill_result.get("meta", {}).get("evidence_refs", []),
                }
            ],
        }
    except Exception as exc:
        _record_run_log({
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
        })
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
