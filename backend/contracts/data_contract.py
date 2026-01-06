# backend/contracts/data_contract.py
"""
数据契约定义 - Phase 0简化版

核心规则：
1. Chapter Generation 只能读专业库，不能读原始解析结果
2. Mapping 是唯一能写专业库的入口（带审计）
3. 所有写入必须携带 evidence_refs + source_hash
4. Validation 是 gating：不通过就降级/追问/拒绝生成
"""

# Phase 0简化版本，后续扩展
__all__ = ["DataContract"]

class DataContract:
    """数据契约 - Phase 0简化版"""
    
    @staticmethod
    def validate_evidence_refs(evidence_refs: list) -> bool:
        """验证evidence_refs结构"""
        required_fields = ["object_key", "type", "page", "source_hash"]
        for ref in evidence_refs:
            if not all(field in ref for field in required_fields):
                return False
        return True
    
    @staticmethod
    def validate_professional_data(data: dict) -> bool:
        """验证专业数据必须包含evidence_refs"""
        return "evidence_refs" in data and len(data.get("evidence_refs", [])) > 0

