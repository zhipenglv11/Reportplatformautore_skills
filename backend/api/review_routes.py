from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import json
import shutil
from pathlib import Path
import os
import uuid

from config import settings
from services.skill_registry.registry import SkillRegistry
from services.llm_gateway.gateway import LLMGateway

router = APIRouter()

# 依赖项
def get_llm_gateway():
    return LLMGateway()

def get_skill_registry():
    registry = SkillRegistry()
    # 确保初始化声明式技能，路径来自 config.settings.declarative_skills_path
    registry.initialize_declarative_skills(Path(settings.declarative_skills_path))
    return registry

async def save_upload_files(files: List[UploadFile], session_id: str, subfolder: str) -> List[str]:
    """保存上传文件到本地，并返回绝对路径列表"""
    file_paths = []
    if not files:
        return file_paths
        
    upload_dir = settings.uploads_path / "review" / session_id / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        file_path = upload_dir / file.filename
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_paths.append(str(file_path.absolute()))
        finally:
            file.file.close()
            
    return file_paths

@router.post("/review")
async def review_files(
    raw_files: List[UploadFile] = File(None),
    report_files: List[UploadFile] = File(None),
    llm_gateway: LLMGateway = Depends(get_llm_gateway),
    registry: SkillRegistry = Depends(get_skill_registry)
):
    """
    原始记录与报告审核入口
    根据上传的文件组合，自动路由到不同的声明式 Skill
    """
    
    # 1. 判空检查
    if not raw_files and not report_files:
        raise HTTPException(status_code=400, detail="至少需要上传一类文件(原始记录或报告)")

    # 生成会话ID
    session_id = str(uuid.uuid4())
    result = {}

    try:
        # 2. 保存文件到本地 (Skills 通常需要文件路径)
        raw_file_paths = await save_upload_files(raw_files, session_id, "raw")
        report_file_paths = await save_upload_files(report_files, session_id, "report")

        # 3. 路由逻辑 & 执行声明式 Skill
        executor = registry._declarative_executor
        if not executor:
             raise HTTPException(status_code=500, detail="声明式技能执行器未初始化")

        skill_result = {}

        if raw_files and report_files:
            # 场景 C: 交叉比对 -> raw-record-vs-report-consistency
            # 构造上下文数据
            context = {
                "raw_records": raw_file_paths,
                "report_document": report_file_paths[0] if report_file_paths else None,
                "session_id": session_id
            }
            # 构造 Prompt 输入 (描述任务)
            user_input = f"""
            Please perform a consistency check between the following raw records and the inspection report.
            Raw Records: {', '.join([Path(p).name for p in raw_file_paths])}
            Report: {Path(report_file_paths[0]).name}
            
            Attached file paths:
            Raw: {raw_file_paths}
            Report: {report_file_paths}
            """
            
            skill_result = await executor.execute(
                skill_name="raw_record_review/raw_record_vs_report_consistency",
                user_input=user_input,
                context=context
            )
            skill_result["mode"] = "cross_check"
            
        elif raw_files:
            # 场景 A: 仅原始记录 -> record_amendment_audit
            context = {
                "files": raw_file_paths,
                "session_id": session_id
            }
            user_input = f"""
            Audit the following raw record files for amendment compliance based on the rules.
            Files: {', '.join([Path(p).name for p in raw_file_paths])}
            
            File Paths: {raw_file_paths}
            """
            
            skill_result = await executor.execute(
                skill_name="raw_record_review/record_amendment_audit",
                user_input=user_input,
                context=context
            )
            skill_result["mode"] = "raw_only"
            
        elif report_files:
            # 场景 B: 仅报告 -> report_audit
            # 注意：report_audit 可能需要文本内容。如果它是纯文本 Skill，我们应该先读取文本。
            # 这里简化处理：直接传路径，假设 Skill 内部或 Agent 知道如何处理（或者我们直接读第一个文件作为 content）
            
            # 尝试读取第一个报告文件的文本内容 (简单处理 UTF-8)
            report_content = ""
            try:
                # 仅作为示例，实际应使用更强的解析器
                if report_file_paths[0].lower().endswith(".txt") or report_file_paths[0].lower().endswith(".md"):
                     report_content = Path(report_file_paths[0]).read_text(encoding='utf-8', errors='ignore')
                else:
                     report_content = f"[File Content Placeholder for {report_file_paths[0]}]"
            except Exception:
                report_content = "[Error reading file content]"

            context = {
                "files": report_file_paths,
                "session_id": session_id
            }
            # report_audit requires 'content' in input usually
            user_input = f"""
            Please audit this report for consistency and format issues.
            File Name: {Path(report_file_paths[0]).name}
            
            Content:
            {report_content}
            """
            
            skill_result = await executor.execute(
                skill_name="raw_record_review/report_audit",
                user_input=user_input,
                context=context
            )
            skill_result["mode"] = "report_only"
            
        # 4. 格式化返回结果
        # DeclarativeSkillExecutor 返回的是 {skill_name, llm_response, script_result, metadata}
        # 前端期望的是 {summary, details: [...], overall_status, mode}
        
        # 尝试从 LLM 响应中解析 JSON
        llm_resp_content = skill_result.get("llm_response", "")
        parsed_json = {}
        try:
            # 清理 Markdown 代码块标记 ```json ... ```
            clean_json = llm_resp_content.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.split("\n", 1)[1]
                if clean_json.endswith("```"):
                    clean_json = clean_json.rsplit("\n", 1)[0]
            parsed_json = json.loads(clean_json)
        except Exception:
            # 如果解析失败，把原始内容放进去
            parsed_json = {"raw_response": llm_resp_content}

        return {
            "summary": parsed_json.get("summary", "审核完成 (详细结果见下方)"),
            "details": parsed_json.get("checks", parsed_json.get("issues", [])), # 兼容不同 Skill 的字段名
            "overall_status": parsed_json.get("overall_status", "pass"),
            "mode": skill_result["mode"],
            "raw_llm_response": llm_resp_content # 调试用
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"审核过程中发生错误: {str(e)}")

