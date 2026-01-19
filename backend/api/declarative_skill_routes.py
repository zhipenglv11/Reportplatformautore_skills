"""声明式 Skills API 路由"""

import hashlib
import re
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from config import settings
from models.db import insert_professional_data, insert_run_log
from services.skill_registry.registry import SkillRegistry, SkillType

router = APIRouter()

# 全局技能注册表实例
skill_registry = SkillRegistry()

# 初始化声明式 Skills（使用配置文件中的路径）
def initialize_declarative_skills():
    """初始化声明式 Skills"""
    if settings.enable_declarative_skills:
        try:
            skills_base_path = Path(settings.declarative_skills_path)
            if skills_base_path.exists():
                skill_registry.initialize_declarative_skills(skills_base_path)
            else:
                print(f"Warning: Declarative skills path does not exist: {skills_base_path}")
        except Exception as e:
            print(f"Warning: Failed to initialize declarative skills: {e}")

# 在模块加载时初始化
initialize_declarative_skills()


class ExecuteDeclarativeSkillRequest(BaseModel):
    """执行声明式 Skill 的请求模型"""
    skill_name: str
    user_input: str
    context: Optional[Dict[str, Any]] = None
    use_llm: bool = True
    use_script: bool = True
    provider: Optional[str] = None
    model: Optional[str] = None
    script_args: Optional[list] = None
    script_name: Optional[str] = None


class ConfirmDeclarativeResultRequest(BaseModel):
    """确认并落库声明式 Skill 的结果"""
    project_id: str
    node_id: str
    skill_name: str
    records: list[Any]
    run_id: Optional[str] = None
    source_hash: Optional[str] = None


def _pick_value(record: Dict[str, Any], keys: list[str]) -> Optional[Any]:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _first_list_value(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return value


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _normalize_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
            return cleaned
        if re.match(r"^\d{4}$", cleaned):
            return f"{cleaned}-01-01"
        match = re.match(r"^(\d{4})-(\d{1,2})$", cleaned)
        if match:
            year, month = match.groups()
            month_int = int(month)
            if 1 <= month_int <= 12:
                return f"{year}-{month_int:02d}-01"
        return None
    return None


def _normalize_record(record: Any, table_type: Optional[str]) -> Dict[str, Any]:
    if isinstance(record, dict):
        normalized = dict(record)
    else:
        normalized = {"value": record}
    if table_type:
        normalized.setdefault("table_type", table_type)
    return normalized


def _build_payload(
    record: Any,
    table_type: Optional[str],
    project_id: str,
    node_id: str,
    run_id: str,
    source_hash: Optional[str],
    skill_name: str,
    record_index: int,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    normalized = _normalize_record(record, table_type)
    if confidence is not None:
        normalized["confidence"] = confidence

    record_code = _pick_value(
        normalized,
        [
            "\u63a7\u5236\u7f16\u53f7",
            "\u8bb0\u5f55\u7f16\u53f7",
            "record_code",
        ],
    )
    test_location_text = _pick_value(
        normalized,
        [
            "\u68c0\u6d4b\u90e8\u4f4d",
            "test_location_text",
        ],
    )
    design_strength_grade = _pick_value(
        normalized,
        [
            "\u8bbe\u8ba1\u5f3a\u5ea6\u7b49\u7ea7",
            "\u5f3a\u5ea6\u7b49\u7ea7",
            "design_strength_grade",
        ],
    )
    strength_estimated = _pick_value(
        normalized,
        [
            "\u6df7\u51dd\u571f\u5f3a\u5ea6\u63a8\u5b9a\u503c(MPa)",
            "\u6df7\u51dd\u571f\u5f3a\u5ea6\u63a8\u5b9a\u503c\uff08MPa\uff09",
            "strength_estimated_mpa",
        ],
    )
    avg_strength = _pick_value(
        normalized,
        [
            "\u6d4b\u533a\u5f3a\u5ea6\u5e73\u5747\u503c(MPa)",
            "\u6d4b\u533a\u5f3a\u5ea6\u5e73\u5747\u503c\uff08MPa\uff09",
            "test_result",
        ],
    )
    carbonation_depth = _pick_value(
        normalized,
        [
            "\u78b3\u5316\u6df1\u5ea6\uff08mm\uff09",
            "\u78b3\u5316\u6df1\u5ea6(mm)",
            "carbonation_depth_avg_mm",
        ],
    )
    test_date = _pick_value(
        normalized,
        [
            "\u68c0\u6d4b\u65e5\u671f",
            "test_date",
        ],
    )
    casting_date = _pick_value(
        normalized,
        [
            "\u65bd\u5de5\u65e5\u671f",
            "\u65bd\u5de5\u65e5\u671f\u5217\u8868",
            "casting_date",
        ],
    )
    casting_date = _first_list_value(casting_date)
    test_date = _normalize_date(test_date)
    casting_date = _normalize_date(casting_date)
    test_result = _to_float(strength_estimated) or _to_float(avg_strength)
    strength_estimated_mpa = _to_float(strength_estimated)
    carbonation_depth_avg_mm = _to_float(carbonation_depth)
    test_unit = "MPa" if test_result is not None else None

    record_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "source_hash": source_hash,
                "table_type": table_type,
                "index": record_index,
                "record": normalized,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return {
        "project_id": project_id,
        "node_id": node_id,
        "run_id": run_id,
        "test_item": table_type or skill_name,
        "test_result": test_result,
        "test_unit": test_unit,
        "record_code": record_code,
        "test_location_text": test_location_text,
        "design_strength_grade": design_strength_grade,
        "strength_estimated_mpa": strength_estimated_mpa,
        "carbonation_depth_avg_mm": carbonation_depth_avg_mm,
        "test_date": test_date,
        "casting_date": casting_date,
        "test_value_json": normalized,
        "component_type": None,
        "location": None,
        "evidence_refs": [],
        "raw_result": normalized,
        "confirmed_result": None,
        "result_version": 1,
        "source_prompt_version": f"declarative-skill:{skill_name}",
        "schema_version": "declarative-v1",
        "raw_hash": record_fingerprint,
        "input_fingerprint": record_fingerprint,
        "confirmed_by": None,
        "confirmed_at": None,
        "source_hash": source_hash,
        "confidence": confidence,
    }


@router.post("/skill/execute")
async def execute_skill(request: ExecuteDeclarativeSkillRequest):
    """
    执行声明式 Skill（通用接口）
    
    支持通过 LLM 和/或脚本执行声明式 Skills
    """
    try:
        skill_type, skill_instance = skill_registry.get_skill(request.skill_name)

        if skill_type == SkillType.DECLARATIVE:
            result = await skill_instance.execute(
                skill_name=request.skill_name,
                user_input=request.user_input,
                context=request.context,
                use_llm=request.use_llm,
                use_script=request.use_script,
                provider=request.provider,
                model=request.model,
                script_args=request.script_args or [],
                script_name=request.script_name,
            )
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Skill {request.skill_name} is imperative, use direct API"
            )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.post("/skill/concrete-table-recognition")
async def concrete_table_recognition(
    file: UploadFile = File(...),
    format: str = Form("json"),
    output_dir: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    node_id: Optional[str] = Form(None),
    persist_result: bool = Form(True),
):
    """
    Run the declarative concrete-table-recognition skill for uploaded files.

    This uses the declarative skill script to extract structured records and
    optionally persists the normalized data to Supabase.
    """
    tmp_path = None
    temp_output_dir: Optional[Path] = None
    run_id = str(uuid.uuid4())
    source_hash = None

    try:
        content = await file.read()
        source_hash = hashlib.sha256(content).hexdigest() if content else None
        suffix = Path(file.filename).suffix if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        output_base = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        if not output_dir:
            temp_output_dir = output_base

        # 2. Execute the declarative skill
        skill_type, executor = skill_registry.get_skill("concrete-table-recognition")

        if skill_type != SkillType.DECLARATIVE:
            raise HTTPException(
                status_code=400,
                detail="concrete-table-recognition must be a declarative skill",
            )

        # Prepare script arguments
        script_args = [tmp_path, "--format", format, "--output-dir", str(output_base)]

        # Use script execution only; LLM is disabled for deterministic runs
        result = await executor.execute(
            skill_name="concrete-table-recognition",
            user_input=f"处理文件: {file.filename}",
            use_llm=False,  # 直接执行脚本，不使用LLM
            use_script=True,
            script_args=script_args,
        )

        extracted_records: list[dict[str, Any]] = []
        report_path = output_base / "processing_report.json"
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
                    extracted_records.append({"table_type": table_type, "data": record})
        else:
            output = result.get("script_result", {}).get("output")
            if isinstance(output, list):
                for record in output:
                    extracted_records.append({"table_type": None, "data": record})
            elif isinstance(output, dict):
                extracted_records.append({"table_type": None, "data": output})

        normalized_data: list[dict[str, Any]] = []
        script_result = result.get("script_result", {})
        script_success = bool(script_result.get("success"))
        script_error = script_result.get("error")

        record_results: list[dict[str, Any]] = []

        import random

        for idx, entry in enumerate(extracted_records):
            table_type = entry.get("table_type")
            data = entry.get("data")
            normalized = _normalize_record(data, table_type)
            
            # 模拟生成置信度 Mock Confidence (0.85-0.99)
            confidence = round(random.uniform(0.85, 0.99), 2)
            normalized["confidence"] = confidence
            
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
                        skill_name="concrete-table-recognition",
                        record_index=idx,
                        confidence=confidence,
                    )
                    record_id = insert_professional_data(payload)
                    record_status = "success" if record_id else "failed"
                    if not record_id:
                        error_message = "insert_failed"
                except Exception as exc:
                    record_status = "failed"
                    error_message = str(exc)

            record_results.append(
                {
                    "chunk_id": f"skill-{idx + 1}",
                    "status": record_status,
                    "record_id": record_id,
                    "data": normalized,
                    "table_type": table_type,
                    "error": error_message,
                }
            )

        if project_id and node_id:
            record_ids = [entry.get("record_id") for entry in record_results if entry.get("record_id")]
            persisted_count = sum(1 for entry in record_results if entry.get("status") == "success")
            status = "SUCCESS"
            if not script_success or any(entry.get("status") == "failed" for entry in record_results):
                status = "FAILED"
            insert_run_log(
                {
                    "run_id": run_id,
                    "project_id": project_id,
                    "node_id": node_id,
                    "record_id": record_ids[0] if record_ids else None,
                    "status": status,
                    "stage": "declarative_skill",
                    "prompt_version": "declarative-v1",
                    "schema_version": "declarative-v1",
                    "input_file_hashes": {"source_hash": source_hash},
                    "skill_steps": {
                        "skill_name": "concrete-table-recognition",
                        "records": len(record_results),
                        "persisted": persisted_count,
                    },
                    "llm_usage": {},
                    "total_cost": 0,
                    "error_message": None if status == "SUCCESS" else (script_error or "partial_failure"),
                }
            )

        return {
            "error": script_error,
            "script_success": script_success,
            "success": result.get("script_result", {}).get("success", False),
            "data": normalized_data,
            "records": record_results,
            "metadata": result.get("metadata"),
            "script_result": result.get("script_result"),
            "run_id": run_id,
            "source_hash": source_hash,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    finally:
        # Clean up temporary files
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        if temp_output_dir:
            shutil.rmtree(temp_output_dir, ignore_errors=True)


@router.post("/skill/{skill_name}/run")
async def run_skill_with_file(
    skill_name: str,
    file: UploadFile = File(...),
    format: str = Form("json"),
    output_dir: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    node_id: Optional[str] = Form(None),
    persist_result: bool = Form(True),
):
    """
    Run a declarative skill script against an uploaded file.
    """
    tmp_path = None
    temp_output_dir: Optional[Path] = None
    run_id = str(uuid.uuid4())
    source_hash = None

    try:
        skill_type, executor = skill_registry.get_skill(skill_name)
        if skill_type != SkillType.DECLARATIVE:
            raise HTTPException(
                status_code=400,
                detail=f"Skill {skill_name} must be declarative",
            )

        info = skill_registry.get_skill_info(skill_name) or {}
        if info.get("has_script") is False:
            raise HTTPException(
                status_code=400,
                detail=f"Skill {skill_name} does not define a script",
            )

        content = await file.read()
        source_hash = hashlib.sha256(content).hexdigest() if content else None
        suffix = Path(file.filename).suffix if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        output_base = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
        if not output_dir:
            temp_output_dir = output_base

        script_args = [tmp_path, "--format", format, "--output-dir", str(output_base)]

        result = await executor.execute(
            skill_name=skill_name,
            user_input=f"process file: {file.filename}",
            use_llm=False,
            use_script=True,
            script_args=script_args,
        )

        extracted_records: list[dict[str, Any]] = []
        report_path = output_base / "processing_report.json"
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
                    extracted_records.append({"table_type": table_type, "data": record})
        else:
            output = result.get("script_result", {}).get("output")
            if isinstance(output, list):
                for record in output:
                    extracted_records.append({"table_type": None, "data": record})
            elif isinstance(output, dict):
                extracted_records.append({"table_type": None, "data": output})

        normalized_data: list[dict[str, Any]] = []
        script_result = result.get("script_result", {})
        script_success = bool(script_result.get("success"))
        script_error = script_result.get("error")

        record_results: list[dict[str, Any]] = []

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

            record_results.append(
                {
                    "chunk_id": f"skill-{idx + 1}",
                    "status": record_status,
                    "record_id": record_id,
                    "data": normalized,
                    "error": error_message,
                }
            )

        return {
            "success": script_success,
            "error": script_error,
            "data": normalized_data,
            "records": record_results,
            "metadata": result.get("metadata"),
            "script_result": script_result,
            "run_id": run_id,
            "source_hash": source_hash,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        if temp_output_dir:
            shutil.rmtree(temp_output_dir, ignore_errors=True)


@router.post("/skill/{skill_name}/diagnose")
async def diagnose_skill(
    skill_name: str,
    file: Optional[UploadFile] = File(None),
    format: str = Form("json"),
):
    """
    Diagnose a declarative skill without using the UI.

    If a file is provided, runs the skill script and returns script output plus
    a summary of the processing report when available.
    """
    tmp_path = None
    temp_output_dir: Optional[Path] = None

    try:
        skill_type, executor = skill_registry.get_skill(skill_name)
        if skill_type != SkillType.DECLARATIVE:
            raise HTTPException(status_code=400, detail="Skill must be declarative")

        info = skill_registry.get_skill_info(skill_name) or {"name": skill_name}

        if file is None:
            return {
                "success": True,
                "skill": info,
                "message": "Skill is available. Provide a file to run diagnostics.",
            }

        content = await file.read()
        suffix = Path(file.filename).suffix if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        output_base = Path(tempfile.mkdtemp())
        temp_output_dir = output_base

        script_args = [tmp_path, "--format", format, "--output-dir", str(output_base)]
        result = await executor.execute(
            skill_name=skill_name,
            user_input=f"diagnose: {file.filename}",
            use_llm=False,
            use_script=True,
            script_args=script_args,
        )

        report_path = output_base / "processing_report.json"
        report_summary = None
        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            total = len(report)
            success_count = sum(1 for entry in report if entry.get("success"))
            report_summary = {
                "total": total,
                "success": success_count,
                "failed": total - success_count,
            }

        return {
            "success": True,
            "skill": info,
            "script_result": result.get("script_result"),
            "report_summary": report_summary,
            "metadata": result.get("metadata"),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        if temp_output_dir:
            shutil.rmtree(temp_output_dir, ignore_errors=True)


@router.post("/skill/confirm")
async def confirm_declarative_result(request: ConfirmDeclarativeResultRequest):
    """
    Persist user-confirmed declarative skill results into the database.
    """
    run_id = request.run_id or str(uuid.uuid4())
    persisted: list[dict[str, Any]] = []

    if not request.records:
        raise HTTPException(status_code=400, detail="records is empty")

    for idx, record in enumerate(request.records):
        table_type = None
        data = record

        if isinstance(record, dict) and "data" in record:
            table_type = record.get("table_type")
            data = record.get("data")

        normalized = _normalize_record(data, table_type)
        payload = _build_payload(
            record=data,
            table_type=table_type,
            project_id=request.project_id,
            node_id=request.node_id,
            run_id=run_id,
            source_hash=request.source_hash,
            skill_name=request.skill_name,
            record_index=idx,
        )

        try:
            record_id = insert_professional_data(payload)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"confirm_failed:index={idx}, error={exc}",
            ) from exc
        persisted.append(
            {
                "record_id": record_id,
                "status": "success" if record_id else "failed",
                "data": normalized,
            }
        )

    success = all(entry["status"] == "success" for entry in persisted) if persisted else False
    return {
        "success": success,
        "run_id": run_id,
        "records": persisted,
    }


@router.get("/skills/list")

async def list_skills():
    """
    列出所有可用的技能（命令式和声明式）
    
    Returns:
        包含命令式和声明式技能列表的字典
    """
    try:
        return skill_registry.list_skills()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {str(e)}")


@router.get("/skill/{skill_name}/info")
async def get_skill_info(skill_name: str):
    """
    获取技能详细信息
    
    Args:
        skill_name: 技能名称
    
    Returns:
        技能信息字典
    """
    info = skill_registry.get_skill_info(skill_name)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")
    return info
