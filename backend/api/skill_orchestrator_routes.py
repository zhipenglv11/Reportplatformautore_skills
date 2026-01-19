"""技能编排器 API 路由：支持批量上传和智能路由"""

import json
import shutil
import tempfile
import uuid
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from config import settings
from services.skill_orchestrator import SkillOrchestrator
from services.skill_registry.registry import SkillRegistry, SkillType
from models.db import insert_professional_data, insert_run_log

# 导入共享的数据处理函数（需要直接导入，因为它们在模块级别）
from api.declarative_skill_routes import _normalize_record, _build_payload

router = APIRouter()

# 全局编排器实例
skill_orchestrator = SkillOrchestrator()
skill_registry = SkillRegistry()


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    total_files: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]


@router.post("/skill/orchestrate")
async def orchestrate_files(
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    node_id: str = Form(...),
    persist_result: bool = Form(True),
    use_llm_classification: bool = Form(True),
):
    """
    智能编排：批量上传文件，自动识别类型并路由到对应技能
    
    流程：
    1. 接收多个文件
    2. 使用 LLM 或规则识别每个文件的类型
    3. 根据文件类型路由到对应的技能
    4. 执行技能提取数据
    5. 提交到数据库（如果 persist_result=True）
    
    Args:
        files: 文件列表
        project_id: 项目ID
        node_id: 节点ID
        persist_result: 是否提交到数据库
        use_llm_classification: 是否使用 LLM 进行文件分类
    
    Returns:
        批量处理结果
    """
    if not files:
        raise HTTPException(status_code=400, detail="至少需要上传一个文件")
    
    run_id = str(uuid.uuid4())
    temp_files: List[Path] = []
    temp_dirs: List[Path] = []
    
    try:
        # 步骤1：保存所有文件到临时目录
        file_info_list = []
        for file in files:
            content = await file.read()
            source_hash = hashlib.sha256(content).hexdigest() if content else None
            suffix = Path(file.filename).suffix if file.filename else ""
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(content)
                tmp_path = Path(tmp_file.name)
                temp_files.append(tmp_path)
            
            file_info_list.append({
                "path": tmp_path,
                "name": file.filename or "unknown",
                "source_hash": source_hash,
            })
        
        # 步骤2：识别文件类型
        classifications = []
        for file_info in file_info_list:
            if use_llm_classification:
                # 使用 LLM 识别
                classification = await skill_orchestrator.classify_file(
                    file_path=file_info["path"],
                    file_name=file_info["name"],
                )
            else:
                # 使用规则匹配
                classification = skill_orchestrator._classify_by_rules(file_info["name"])
            
            classifications.append({
                "file_info": file_info,
                "classification": classification,
            })
        
        # 步骤3：按技能分组并执行
        skill_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in classifications:
            skill_name = item["classification"].skill_name
            if skill_name:
                if skill_name not in skill_groups:
                    skill_groups[skill_name] = []
                skill_groups[skill_name].append(item)
        
        # 步骤4：执行每个技能组
        all_results = []
        all_record_results = []
        
        for skill_name, file_group in skill_groups.items():
            # 获取技能执行器
            try:
                skill_type, executor = skill_registry.get_skill(skill_name)
            except ValueError as e:
                # 技能不存在，记录错误
                for item in file_group:
                    all_results.append({
                        "file_name": item["file_info"]["name"],
                        "classification": {
                            "file_type": item["classification"].file_type,
                            "skill_name": skill_name,
                            "confidence": item["classification"].confidence,
                            "reasoning": item["classification"].reasoning,
                        },
                        "success": False,
                        "error": f"技能不存在: {skill_name}",
                        "data": None,
                        "records": [],
                    })
                continue
            
            if skill_type != SkillType.DECLARATIVE:
                for item in file_group:
                    all_results.append({
                        "file_name": item["file_info"]["name"],
                        "classification": {
                            "file_type": item["classification"].file_type,
                            "skill_name": skill_name,
                            "confidence": item["classification"].confidence,
                            "reasoning": item["classification"].reasoning,
                        },
                        "success": False,
                        "error": f"技能 {skill_name} 不是声明式技能",
                        "data": None,
                        "records": [],
                    })
                continue
            
            # 为每个文件执行技能
            for item in file_group:
                file_info = item["file_info"]
                classification = item["classification"]
                file_path = file_info["path"]
                file_name = file_info["name"]
                source_hash = file_info["source_hash"]
                
                try:
                    # 创建临时输出目录
                    output_dir = Path(tempfile.mkdtemp())
                    temp_dirs.append(output_dir)
                    
                    # 执行技能
                    script_args = [
                        str(file_path),
                        "--format", "json",
                        "--output-dir", str(output_dir),
                    ]
                    
                    skill_result = await executor.execute(
                        skill_name=skill_name,
                        user_input=f"处理文件: {file_name}",
                        use_llm=False,
                        use_script=True,
                        script_args=script_args,
                    )
                    
                    # 处理脚本输出
                    extracted_records = []
                    report_path = output_dir / "processing_report.json"
                    
                    if report_path.exists():
                        report = json.loads(report_path.read_text(encoding="utf-8"))
                        for entry in report:
                            if not entry.get("success"):
                                continue
                            table_type = entry.get("type")
                            data = entry.get("data") or []
                            if isinstance(data, dict):
                                data = [data]
                            for record in data:
                                extracted_records.append({
                                    "table_type": table_type,
                                    "data": record,
                                })
                    else:
                        output = skill_result.get("script_result", {}).get("output")
                        if isinstance(output, list):
                            for record in output:
                                extracted_records.append({
                                    "table_type": None,
                                    "data": record,
                                })
                        elif isinstance(output, dict):
                            extracted_records.append({
                                "table_type": None,
                                "data": output,
                            })
                    
                    # 规范化数据并提交数据库
                    normalized_data = []
                    record_results = []
                    
                    for idx, entry in enumerate(extracted_records):
                        table_type = entry.get("table_type")
                        data = entry.get("data")
                        normalized = _normalize_record(data, table_type)
                        normalized_data.append(normalized)
                        
                        record_status = "skipped"
                        record_id = None
                        error_message = None
                        
                        if persist_result and project_id and node_id:
                            try:
                                payload = _build_payload(
                                    record=data,
                                    table_type=table_type,
                                    project_id=project_id,
                                    node_id=node_id,
                                    run_id=run_id,
                                    source_hash=source_hash,
                                    skill_name=skill_name,
                                    record_index=idx,
                                )
                                record_id = insert_professional_data(payload)
                                record_status = "success" if record_id else "failed"
                                if not record_id:
                                    error_message = "insert_failed"
                            except Exception as exc:
                                record_status = "failed"
                                error_message = str(exc)
                        
                        record_results.append({
                            "chunk_id": f"skill-{idx + 1}",
                            "status": record_status,
                            "record_id": record_id,
                            "data": normalized,
                            "table_type": table_type,
                            "error": error_message,
                        })
                        all_record_results.extend(record_results)
                    
                    # 记录执行日志
                    if project_id and node_id:
                        record_ids = [r.get("record_id") for r in record_results if r.get("record_id")]
                        persisted_count = sum(1 for r in record_results if r.get("status") == "success")
                        script_success = skill_result.get("script_result", {}).get("success", False)
                        status = "SUCCESS" if script_success and persisted_count > 0 else "FAILED"
                        
                        insert_run_log({
                            "run_id": run_id,
                            "project_id": project_id,
                            "node_id": node_id,
                            "record_id": record_ids[0] if record_ids else None,
                            "status": status,
                            "stage": "orchestrated_skill",
                            "prompt_version": "orchestrator-v1",
                            "schema_version": "orchestrator-v1",
                            "input_file_hashes": {"source_hash": source_hash},
                            "skill_steps": {
                                "skill_name": skill_name,
                                "file_type": classification.file_type,
                                "records": len(record_results),
                                "persisted": persisted_count,
                            },
                            "llm_usage": {},
                            "total_cost": 0,
                            "error_message": None if status == "SUCCESS" else "partial_failure",
                        })
                    
                    all_results.append({
                        "file_name": file_name,
                        "classification": {
                            "file_type": classification.file_type,
                            "skill_name": skill_name,
                            "confidence": classification.confidence,
                            "reasoning": classification.reasoning,
                        },
                        "success": True,
                        "data": normalized_data,
                        "records": record_results,
                        "metadata": skill_result.get("metadata"),
                    })
                    
                except Exception as e:
                    all_results.append({
                        "file_name": file_name,
                        "classification": {
                            "file_type": classification.file_type,
                            "skill_name": skill_name,
                            "confidence": classification.confidence,
                            "reasoning": classification.reasoning,
                        },
                        "success": False,
                        "error": str(e),
                        "data": None,
                        "records": [],
                    })
        
        # 处理没有匹配技能的文件
        for item in classifications:
            if not item["classification"].skill_name:
                all_results.append({
                    "file_name": item["file_info"]["name"],
                    "classification": {
                        "file_type": item["classification"].file_type,
                        "skill_name": None,
                        "confidence": item["classification"].confidence,
                        "reasoning": item["classification"].reasoning,
                    },
                    "success": False,
                    "error": f"未找到匹配的技能，文件类型: {item['classification'].file_type}",
                    "data": None,
                    "records": [],
                })
        
        # 统计结果
        successful = sum(1 for r in all_results if r.get("success"))
        failed = len(all_results) - successful
        
        return {
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "run_id": run_id,
            "results": all_results,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编排执行失败: {str(e)}")
    finally:
        # 清理临时文件
        for tmp_path in temp_files:
            tmp_path.unlink(missing_ok=True)
        for tmp_dir in temp_dirs:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/skill/classify")
async def classify_file(
    file: UploadFile = File(...),
    use_llm: bool = Form(True),
):
    """
    仅识别文件类型（不执行技能）
    
    用于测试文件分类功能
    """
    import tempfile
    
    tmp_path = None
    try:
        content = await file.read()
        suffix = Path(file.filename).suffix if file.filename else ""
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        if use_llm:
            classification = await skill_orchestrator.classify_file(
                file_path=tmp_path,
                file_name=file.filename or "unknown",
            )
        else:
            classification = skill_orchestrator._classify_by_rules(
                file.filename or "unknown"
            )
        
        return {
            "file_name": file.filename,
            "classification": {
                "file_type": classification.file_type,
                "skill_name": classification.skill_name,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
            },
        }
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)
