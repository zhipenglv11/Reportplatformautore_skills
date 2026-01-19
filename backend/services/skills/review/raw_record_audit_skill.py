from typing import Dict, Any, List
from services.skill_registry.registry import BaseSkill
from services.llm_gateway.gateway import LLMGateway
from services.skills.review.audit_tools import AuditTools

class RawRecordAuditSkill(BaseSkill):
    """
    技能：原始记录审核
    场景：用户仅上传了原始记录文件。
    目标：检查计算逻辑正确性、记录规范性。
    """
    name = "audit_raw_record"
    description = "审核原始记录的合规性与计算逻辑"

    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
        self.tools = AuditTools()

    async def execute(self, files: List[Any], **kwargs) -> Dict[str, Any]: 
        """
        执行审核逻辑
        :param files: 原始记录文件列表
        """
        results = []
        
        # 1. 遍历每个文件进行 OCR 或 数据提取 (假设已有提取服务或在此调用)
        # 这里模拟提取过程
        for file in files:
            file_result = {
                "file_name": getattr(file, "filename", "unknown"),
                "issues": [],
                "status": "pass"
            }
            
            # TODO: 实现具体的审核逻辑
            # 示例：检查是否包含必须的字段
            # extracted_data = await self._extract_data(file)
            # if not extracted_data.get("record_number"):
            #    file_result["issues"].append("缺少原始记录编号")
            
            results.append(file_result)

        return {
            "summary": "原始记录审核完成",
            "details": results,
            "overall_status": "warning" if any(r["issues"] for r in results) else "pass"
        }

    async def _extract_data(self, file) -> Dict[str, Any]:
        # 占位：调用 LLM 或 OCR 提取数据
        return {}
