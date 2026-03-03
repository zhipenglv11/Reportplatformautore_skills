# backend/api/collection_routes.py
"""
Collection upload routes for Phase 0.
"""
from datetime import datetime
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from config import settings
from core.llm.gateway import LLMGateway
from collection.services.skills.ingest_skill import IngestSkill
from collection.services.skills.parse_skill import ParseSkill
from collection.services.skills.template_profile_skill import TemplateProfileSkill
from collection.services.template_resolver import TemplateResolver
from collection.services.skills.mapping_skill import MappingSkill
from collection.services.skills.validation_skill import ValidationSkill
from core.models.template_registry import fetch_template_by_id
from core.models.db import insert_professional_data, insert_run_log

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "image/webp",
}
MAX_FILE_SIZE = 50 * 1024 * 1024

DEFAULT_PROMPT = """# 回弹法检测表结构化抽取 Skill Prompt（稳定性优先）

## 角色
你是建筑工程质量检测领域的专业抽取引擎，熟悉 JGJ/T 23-2011。
你的首要目标是输出可靠数据，而不是尽量多输出。
不确定时允许输出 null，禁止猜测。

## 输入
输入为一张或多张《回弹法检测混凝土强度原始记录表》扫描图片。
图片可能存在模糊、倾斜、曝光不均或手写干扰。

## 任务
对每一张检测表独立完成字段抽取、校验、计算，并输出 JSON。
任一步失败，不得强行推断。

## 必须输出字段
- record_code（表格左上角或页眉处的原始记录编号）
- 检测部位
- 检测日期
- 设计强度等级
- 混凝土强度推定值_MPa
- 碳化深度计算值_mm（数组）
- 碳化深度平均值_mm

## 字段抽取规则

### record_code
- 来源：表格左上角或页眉处的原始记录编号（如 KSQR-4.13-XC-10）
- 原样输出，不做改写
- 无法识别则为 null

### 检测部位
- 来源：表头字段“检测部位”
- 原样输出，不补全、不改写
- 无法完整识别则为 null

### 检测日期
- 来源：表头字段“检测日期/测试日期”
- 原样输出，无法识别则为 null

### 设计强度等级
- 来源：表头字段“设计强度等级”
- 合法格式：C + 数字（如 C30）
- 只允许表头来源，其它位置忽略

### 混凝土强度推定值_MPa
- 来源：表格右下角“混凝土强度推定值（MPa）”
- 必须为数值型
- 若明显异常（低于测区平均值 5MPa 以上），输出 null

### 碳化深度计算值_mm
- 必须识别到“碳化深度(mm)”及子列“测值 / 计算”
- 只允许使用“计算”列
- 每测区最多 1 个值
- 缺失的测区直接跳过
- 有效测区 < 5 时，字段整体为 null

### 碳化深度平均值_mm
- 仅基于碳化深度计算值_mm 计算
- 公式：平均值 = 数组求和 / 数量
- 不允许直接抄表中已有平均值
- 数组为空则为 null

## 输出格式
- 仅输出 JSON
- 多张表输出为 JSON 数组
- 单张表输出为一个对象
- 数值字段必须输出 number 或 null，不得输出字符串

示例结构：
{
  "检测部位": "...",
  "设计强度等级": "C30",
  "混凝土强度推定值_MPa": 0.0,
  "碳化深度计算值_mm": [],
  "碳化深度平均值_mm": 0.0
}

## 稳定性硬约束
- 不得猜测、不补齐、不基于经验推断
- 不得使用测值代替计算值
- 不得跨表合并数据
- 宁可输出 null，不可输出错误数值
"""


class ConfirmRequest(BaseModel):
    project_id: str
    node_id: str
    run_id: Optional[str] = None
    mapped_payload: dict


class CommitRequest(BaseModel):
    project_id: str
    node_id: str
    object_key: str
    source_hash: str
    filename: Optional[str] = None
    template_id: Optional[str] = None
    selections: Optional[object] = None
    use_llm: bool = True
    persist_result: bool = True
    run_id: Optional[str] = None


def _hash_record_instance(source_hash: str, chunk_id: str, template_id: str, schema_version: str) -> str:
    raw = f"{source_hash}:{chunk_id}:{template_id}:{schema_version}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_chunk_pages(chunk_id: str, selection: dict, total_pages: int) -> Optional[list[int]]:
    if selection.get("page_range"):
        page_range = selection.get("page_range")
        if isinstance(page_range, list) and page_range:
            if len(page_range) == 1:
                return [int(page_range[0])]
            start, end = int(page_range[0]), int(page_range[-1])
            if 1 <= start <= end <= total_pages:
                return list(range(start, end + 1))
    if chunk_id.startswith("page-"):
        try:
            page_index = int(chunk_id.split("-", 1)[1])
        except ValueError:
            return None
        return [page_index] if 1 <= page_index <= total_pages else None
    if chunk_id.startswith("chunk-"):
        parts = chunk_id.split("-")[1:]
        try:
            if len(parts) == 1:
                page_index = int(parts[0])
                return [page_index] if 1 <= page_index <= total_pages else None
            if len(parts) >= 2:
                start, end = int(parts[0]), int(parts[1])
                if 1 <= start <= end <= total_pages:
                    return list(range(start, end + 1))
        except ValueError:
            return None
    return None


@router.post("/collection/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    node_id: str = Form(...),
    node_label: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    template_id: Optional[str] = Form(None),
    auto_parse: bool = Form(True),
    use_llm: bool = Form(True),
    persist_result: bool = Form(False),
):
    """Upload a file and optionally parse it immediately."""
    try:
        run_id = None
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file type: {ext}. Only PDF and images are allowed.",
                )

        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {file.content_type}",
            )

        content = await file.read()
        file_size = len(content)
        await file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds 50MB limit.",
            )

        ingest_skill = IngestSkill()
        ingest_result = await ingest_skill.execute(file, project_id)
        run_id = str(uuid.uuid4())
        insert_run_log(
            {
                "run_id": run_id,
                "project_id": project_id,
                "node_id": node_id,
                "record_id": None,
                "status": "SUCCESS",
                "stage": "ingest",
                "prompt_version": None,
                "schema_version": "v1",
                "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                "skill_steps": {"object_key": ingest_result["object_key"]},
                "llm_usage": {},
                "total_cost": 0,
                "error_message": None,
            }
        )

        file_type = "pdf" if file.filename and file.filename.lower().endswith(".pdf") else "image"

        result = {
            "project_id": project_id,
            "node_id": node_id,
            "object_key": ingest_result["object_key"],
            "source_hash": ingest_result["source_hash"],
            "filename": ingest_result["filename"],
            "file_type": file_type,
            "file_size": file_size,
            "upload_date": datetime.now().isoformat(),
            "run_id": run_id,
        }

        if auto_parse:
            llm_gateway = LLMGateway()
            parse_skill = ParseSkill(llm_gateway=llm_gateway)
            prompt_label = node_label or node_id
            llm_prompt = prompt or DEFAULT_PROMPT + f"\n\n# 当前节点\n{prompt_label}"
            parse_result = await parse_skill.execute(
                ingest_result=ingest_result,
                use_llm=False,
            )
            template_profile = None
            resolved_template = None
            if use_llm:
                profile_skill = TemplateProfileSkill(llm_gateway=llm_gateway)
                template_profile = await profile_skill.execute(parse_result.get("page_images", []))
                resolver = TemplateResolver()
                resolved_template = resolver.resolve(
                    fingerprint=template_profile.get("fingerprint"),
                    template_id=template_id,
                )
                insert_run_log(
                    {
                        "run_id": run_id,
                        "project_id": project_id,
                        "node_id": node_id,
                        "record_id": None,
                        "status": "SUCCESS" if resolved_template else "FAILED",
                        "stage": "template_resolve",
                        "prompt_version": None,
                        "schema_version": "v1",
                        "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                        "skill_steps": {
                            "fingerprint": template_profile.get("fingerprint"),
                            "template_id": resolved_template.get("template_id") if resolved_template else None,
                        },
                        "llm_usage": {},
                        "total_cost": 0,
                        "error_message": None if resolved_template else "unknown_template",
                    }
                )
                if not resolved_template:
                    result["template_resolution"] = {
                        "status": "unknown_template",
                        "profile": template_profile,
                    }
                    result["parse_result"] = {
                        "parse_id": parse_result["parse_id"],
                        "structured_data": {},
                        "evidence_refs": parse_result.get("evidence_refs", []),
                        "page_images_count": len(parse_result.get("page_images", [])),
                    }
                    return result
                llm_prompt = resolved_template.get("prompt") or llm_prompt
                llm_response = await llm_gateway.vision_completion(
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    images=parse_result.get("page_images", []),
                    prompt=llm_prompt,
                    response_format={"type": "json_object"},
                )
                raw_content = llm_response.get("content", {})
                if isinstance(raw_content, str):
                    try:
                        parse_result["structured_data"] = json.loads(raw_content)
                    except json.JSONDecodeError:
                        parse_result["structured_data"] = {}
                        parse_result["parse_error"] = "structured_data is not valid JSON"
                        parse_result["structured_data_raw"] = raw_content
                else:
                    parse_result["structured_data"] = raw_content
                parse_result["llm_usage"] = llm_response.get("usage", {})
                result["template_resolution"] = {
                    "status": "matched",
                    "template_id": resolved_template.get("template_id"),
                    "dataset_key": resolved_template.get("dataset_key"),
                    "fingerprint": resolved_template.get("fingerprint"),
                }
            result["parse_result"] = {
                "parse_id": parse_result["parse_id"],
                "structured_data": parse_result.get("structured_data", {}),
                "evidence_refs": parse_result.get("evidence_refs", []),
                "page_images_count": len(parse_result.get("page_images", [])),
            }
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": None,
                    "status": "SUCCESS",
                    "stage": "parse",
                    "prompt_version": "v1",
                    "schema_version": "v1",
                    "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                    "skill_steps": {"parse_id": parse_result["parse_id"]},
                    "llm_usage": parse_result.get("llm_usage", {}),
                    "total_cost": 0,
                    "error_message": None,
                }
            )
            mapping_skill = MappingSkill()
            mapping_result = mapping_skill.execute(
                project_id=project_id,
                node_id=node_id,
                source_hash=ingest_result["source_hash"],
                structured_data=parse_result.get("structured_data"),
                evidence_refs=parse_result.get("evidence_refs"),
                run_id=run_id,
                test_item_override=node_label,
            )
            if resolved_template:
                mapping_result["mapped"]["test_value_json"] = mapping_result["mapped"].get("test_value_json") or {}
                mapping_result["mapped"]["test_value_json"]["template_id"] = resolved_template.get("template_id")
                mapping_result["mapped"]["test_value_json"]["dataset_key"] = resolved_template.get("dataset_key")
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": None,
                    "status": "SUCCESS",
                    "stage": "mapping",
                    "prompt_version": "v1",
                    "schema_version": "v1",
                    "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                    "skill_steps": {"test_item": mapping_result["mapped"].get("test_item")},
                    "llm_usage": {},
                    "total_cost": 0,
                    "error_message": None,
                }
            )
            validation_rules = resolved_template.get("validation_rules") if resolved_template else None
            validation_skill = ValidationSkill(rules_override=validation_rules)
            validation_result = validation_skill.execute(
                mapping_result["mapped"],
                mapping_result.get("meta"),
            )
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": None,
                    "status": "SUCCESS" if validation_result.is_valid else "FAILED",
                    "stage": "validation",
                    "prompt_version": "v1",
                    "schema_version": "v1",
                    "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                    "skill_steps": {
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                    },
                    "llm_usage": {},
                    "total_cost": 0,
                    "error_message": None if validation_result.is_valid else "; ".join(validation_result.errors),
                }
            )
            result["validation_result"] = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "policy": validation_result.policy,
            }
            result["mapping_payload"] = mapping_result["mapped"]
            result["mapping_result"] = {
                "record_id": None,
            }
            if persist_result and validation_result.is_valid:
                record_id = insert_professional_data(validation_result.normalized)
                insert_run_log(
                    {
                        "run_id": run_id,
                        "project_id": project_id,
                        "node_id": node_id,
                        "record_id": record_id,
                        "status": "SUCCESS",
                        "stage": "persist",
                        "prompt_version": "v1",
                        "schema_version": "v1",
                        "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
                        "skill_steps": {"record_id": record_id},
                        "llm_usage": {},
                        "total_cost": 0,
                        "error_message": None,
                    }
                )
                result["mapping_result"] = {
                    "record_id": record_id,
                }

        return result
    except HTTPException as exc:
        if run_id:
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": None,
                    "status": "FAILED",
                    "stage": "exception",
                    "prompt_version": "v1",
                    "schema_version": "v1",
                    "input_file_hashes": {},
                    "skill_steps": {},
                    "llm_usage": {},
                    "total_cost": 0,
                    "error_message": exc.detail if hasattr(exc, "detail") else str(exc),
                }
            )
        raise
    except Exception as exc:
        if run_id:
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": None,
                    "status": "FAILED",
                    "stage": "exception",
                    "prompt_version": "v1",
                    "schema_version": "v1",
                    "input_file_hashes": {},
                    "skill_steps": {},
                    "llm_usage": {},
                    "total_cost": 0,
                    "error_message": str(exc),
                }
            )
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")


@router.post("/ingest/preview")
async def ingest_preview(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    node_id: str = Form(...),
    template_id: Optional[str] = Form(None),
):
    """Parse and optionally extract using a specified template (skipping profiling)."""
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {ext}. Only PDF and images are allowed.",
            )

    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}",
        )

    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds 50MB limit.",
        )

    ingest_skill = IngestSkill()
    ingest_result = await ingest_skill.execute(file, project_id)
    run_id = str(uuid.uuid4())
    insert_run_log(
        {
            "run_id": run_id,
            "project_id": project_id,
            "node_id": node_id,
            "record_id": None,
            "status": "SUCCESS",
            "stage": "ingest_preview",
            "prompt_version": None,
            "schema_version": "v1",
            "input_file_hashes": {"source_hash": ingest_result["source_hash"]},
            "skill_steps": {"object_key": ingest_result["object_key"]},
            "llm_usage": {},
            "total_cost": 0,
            "error_message": None,
        }
    )

    llm_gateway = LLMGateway()
    parse_skill = ParseSkill(llm_gateway=llm_gateway)
    parse_result = await parse_skill.execute(
        ingest_result=ingest_result,
        use_llm=False,
    )
    
    page_images = parse_result.get("page_images", []) or []
    evidence_refs = parse_result.get("evidence_refs", []) or []

    # If template_id is provided, skip profiling and go straight to extraction
    extracted_data_map = {}
    resolved_template_id = template_id
    
    # If no template_id provided, we just parse pages and return chunks (manual selection mode)
    # We do NOT run profiling automatically anymore as requested.

    if resolved_template_id:
        template = fetch_template_by_id(resolved_template_id)
        if template:
            llm_prompt = template.get("prompt") or DEFAULT_PROMPT
            # Extract data for all pages at once (or chunk by chunk if needed, here we do simple 1-pass for preview)
            # Note: For multi-page PDFs, this might need refinement to handle per-page or merged extraction.
            # Here we treat all pages as one extraction context for simplicity unless split.
            
            # Simple strategy: Extract from all images
            llm_response = await llm_gateway.vision_completion(
                provider=settings.llm_provider,
                model=settings.llm_model,
                images=page_images,
                prompt=llm_prompt,
                response_format={"type": "json_object"},
            )
            raw_content = llm_response.get("content", {})
            structured_data = {}
            if isinstance(raw_content, str):
                try:
                    structured_data = json.loads(raw_content)
                except json.JSONDecodeError:
                    structured_data = {}
            else:
                structured_data = raw_content
            
            # Associate this data with the "whole file" or first chunk
            extracted_data_map["global"] = structured_data

    chunks = []
    # Create simple page-based chunks
    for i, _ in enumerate(page_images):
        page_num = i + 1
        chunk_id = f"page-{page_num}"
        chunk_evidence = next((ref for ref in evidence_refs if ref.get("page") == page_num), None)
        
        # In manual mode, we just list the pages. 
        # If extraction happened (template provided), we attach the data.
        # For simplicity, if we extracted globally, we attach it to the first chunk or replicate?
        # Let's attach to the first chunk for now or all if 1 page.
        
        data_preview = None
        if resolved_template_id and i == 0: 
             data_preview = extracted_data_map.get("global")

        chunks.append({
            "chunk_id": chunk_id,
            "page_range": [page_num],
            "template_code": None,
            "record_code": None,
            "fingerprint": None, # Skipped
            "suggested_template_id": resolved_template_id, # If user selected it
            "candidate_templates": [],
            "candidates": [],
            "profile": {
                "title": None,
                "headers": [],
                "fingerprint": None
            }, # Empty profile
            "evidence_refs": [chunk_evidence] if chunk_evidence else [],
            "structured_data": data_preview # The actual extracted data
        })

    return {
        "run_id": run_id,
        "project_id": project_id,
        "node_id": node_id,
        "object_key": ingest_result["object_key"],
        "source_hash": ingest_result["source_hash"],
        "filename": ingest_result["filename"],
        "file_type": parse_result.get("file_type"),
        "file_size": file_size,
        "chunks": chunks,
    }


@router.post("/ingest/commit")
async def ingest_commit(request: CommitRequest):
    """Extract and persist using a confirmed template."""
    run_id = request.run_id or str(uuid.uuid4())
    ingest_result = {
        "object_key": request.object_key,
        "source_hash": request.source_hash,
        "filename": request.filename or Path(request.object_key).name,
    }

    try:
        llm_gateway = LLMGateway()
        parse_skill = ParseSkill(llm_gateway=llm_gateway)
        parse_result = await parse_skill.execute(
            ingest_result=ingest_result,
            use_llm=False,
        )

        selections = request.selections or []
        if isinstance(selections, dict):
            selections = [{"chunk_id": chunk_id, "template_id": template_id} for chunk_id, template_id in selections.items()]
        # If selections is a list, we assume it's already in the correct format
        
        if not selections and request.template_id:
            selections = [{"chunk_id": "page-1", "template_id": request.template_id}]
        
        # Fallback: if user didn't select anything but we have a single template scenario
        if not selections:
            # Try to see if we can just commit everything with the default template if valid? 
            # For now, strict check.
            pass

        if not selections:
            raise HTTPException(status_code=400, detail="missing_template_selection")

        page_images = parse_result.get("page_images", []) or []
        evidence_refs = parse_result.get("evidence_refs", []) or []
        results = []

        mapping_skill = MappingSkill()

        for selection in selections:
            chunk_id = selection.get("chunk_id")
            template_id = selection.get("template_id")
            if not chunk_id or not template_id:
                continue
            template = fetch_template_by_id(template_id)
            if not template:
                results.append(
                    {
                        "chunk_id": chunk_id,
                        "template_id": template_id,
                        "status": "failed",
                        "error": "unknown_template",
                    }
                )
                continue

            pages = _parse_chunk_pages(chunk_id, selection, len(page_images))
            if not pages:
                results.append(
                    {
                        "chunk_id": chunk_id,
                        "template_id": template_id,
                        "status": "failed",
                        "error": "invalid_chunk",
                    }
                )
                continue

            images = [page_images[page_index - 1] for page_index in pages]
            llm_usage = {}
            structured_data = {}
            
            # Re-run extraction for commit to ensure data freshness and integrity
            if request.use_llm:
                llm_prompt = template.get("prompt") or DEFAULT_PROMPT
                llm_response = await llm_gateway.vision_completion(
                    provider=settings.llm_provider,
                    model=settings.llm_model,
                    images=images,
                    prompt=llm_prompt,
                    response_format={"type": "json_object"},
                )
                raw_content = llm_response.get("content", {})
                if isinstance(raw_content, str):
                    try:
                        structured_data = json.loads(raw_content)
                    except json.JSONDecodeError:
                        structured_data = {}
                else:
                    structured_data = raw_content
                llm_usage = llm_response.get("usage", {})

            chunk_evidence = [ref for ref in evidence_refs if ref.get("page") in pages]

            mapping_result = mapping_skill.execute(
                project_id=request.project_id,
                node_id=request.node_id,
                source_hash=request.source_hash,
                structured_data=structured_data,
                evidence_refs=chunk_evidence,
                run_id=run_id,
                test_item_override=None,
                mapping_override=template.get("mapping_rules"),
            )
            mapping_result["mapped"]["test_value_json"] = mapping_result["mapped"].get("test_value_json") or {}
            mapping_result["mapped"]["test_value_json"]["template_id"] = template.get("template_id")
            mapping_result["mapped"]["test_value_json"]["dataset_key"] = template.get("dataset_key")
            record_instance_id = _hash_record_instance(
                request.source_hash,
                chunk_id,
                template_id,
                template.get("schema_version") or "v1",
            )
            mapping_result["mapped"]["test_value_json"]["record_instance_id"] = record_instance_id
            mapping_result["mapped"]["input_fingerprint"] = record_instance_id

            validation_skill = ValidationSkill(rules_override=template.get("validation_rules"))
            validation_result = validation_skill.execute(
                mapping_result["mapped"],
                mapping_result.get("meta"),
            )

            record_id = None
            deduped = False
            
            # Only persist if validation passed
            if request.persist_result and validation_result.is_valid:
                from core.models.db import fetch_record_id_by_fingerprint

                record_id = fetch_record_id_by_fingerprint(
                    input_fingerprint=record_instance_id,
                )
                if record_id:
                    deduped = True
                else:
                    record_id = insert_professional_data(validation_result.normalized)

            results.append(
                {
                    "chunk_id": chunk_id,
                    "template_id": template_id,
                    "status": "success" if validation_result.is_valid else "failed",
                    "record_id": record_id,
                    "inserted_record_ids": [record_id] if record_id and not deduped else [],
                    "deduped": deduped,
                    "data": validation_result.normalized,
                    "validation_result": {
                        "is_valid": validation_result.is_valid,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                        "policy": validation_result.policy,
                    },
                }
            )

            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": request.project_id,
                    "node_id": request.node_id,
                    "record_id": record_id,
                    "status": "SUCCESS" if validation_result.is_valid else "FAILED",
                    "stage": "commit",
                    "prompt_version": template.get("prompt_version"),
                    "schema_version": template.get("schema_version"),
                    "input_file_hashes": {"source_hash": request.source_hash},
                    "skill_steps": {"chunk_id": chunk_id, "template_id": template_id},
                    "llm_usage": llm_usage,
                    "total_cost": 0,
                    "error_message": None if validation_result.is_valid else "; ".join(validation_result.errors),
                }
            )

        return {
            "run_id": run_id,
            "results": results,
        }
    
    except Exception as exc:
        insert_run_log(
            {
                "run_id": run_id,
                "project_id": request.project_id,
                "node_id": request.node_id,
                "record_id": None,
                "status": "FAILED",
                "stage": "exception",
                "prompt_version": "v1",
                "schema_version": "v1",
                "input_file_hashes": {},
                "skill_steps": {},
                "llm_usage": {},
                "total_cost": 0,
                "error_message": f"Commit failed: {str(exc)}",
            }
        )
        raise HTTPException(status_code=500, detail=f"Commit failed: {str(exc)}")


@router.post("/collection/confirm")
async def confirm_result(request: ConfirmRequest):
    """Confirm and persist mapped payload after user approval."""
    run_id = request.run_id or str(uuid.uuid4())
    template_id = (
        request.mapped_payload.get("test_value_json", {}).get("template_id")
        if isinstance(request.mapped_payload.get("test_value_json"), dict)
        else None
    )
    template = fetch_template_by_id(template_id) if template_id else None
    validation_rules = template.get("validation_rules") if template else None
    validation_skill = ValidationSkill(rules_override=validation_rules)
    validation_result = validation_skill.execute(request.mapped_payload, {})

    insert_run_log(
        {
            "run_id": run_id,
            "project_id": request.project_id,
            "node_id": request.node_id,
            "record_id": None,
            "status": "SUCCESS" if validation_result.is_valid else "FAILED",
            "stage": "confirm",
            "prompt_version": "v1",
            "schema_version": "v1",
            "input_file_hashes": {},
            "skill_steps": {
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
            },
            "llm_usage": {},
            "total_cost": 0,
            "error_message": None if validation_result.is_valid else "; ".join(validation_result.errors),
        }
    )

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "validation_failed",
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "policy": validation_result.policy,
            },
        )

    record_id = insert_professional_data(validation_result.normalized)
    insert_run_log(
        {
            "run_id": run_id,
            "project_id": request.project_id,
            "node_id": request.node_id,
            "record_id": record_id,
            "status": "SUCCESS",
            "stage": "persist",
            "prompt_version": "v1",
            "schema_version": "v1",
            "input_file_hashes": {},
            "skill_steps": {"record_id": record_id},
            "llm_usage": {},
            "total_cost": 0,
            "error_message": None,
        }
    )

    return {
        "record_id": record_id,
        "run_id": run_id,
        "validation_result": {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "policy": validation_result.policy,
        },
    }
