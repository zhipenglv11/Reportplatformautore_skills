"""
Data Schema for Structure Damage and Alterations Extraction
结构损伤及拆改检查数据模式定义
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class MetaData:
    """表头元数据"""
    control_id: Optional[str] = None  # 控制编号
    record_no: Optional[str] = None  # 原始记录编号 (No:xxxxx)
    instrument_id: Optional[str] = None  # 仪器编号
    test_date: Optional[str] = None  # 检测日期
    house_name: Optional[str] = None  # 房屋名称


@dataclass
class ItemData:
    """表格项数据 - 每一行一个对象"""
    modification_location: Optional[str] = None  # 拆改部位
    modification_description: Optional[str] = None  # 拆改内容描述（整段原文，不改写）
    photo_no: Optional[str] = None  # 照片编号


@dataclass
class SignoffData:
    """签名信息"""
    inspector: Optional[str] = None  # 检查人
    recorder: Optional[str] = None  # 记录人
    reviewer: Optional[str] = None  # 审核人


@dataclass
class StructureAlterationSchema:
    """结构损伤及拆改检查完整数据模式"""
    meta: MetaData = field(default_factory=MetaData)
    items: List[ItemData] = field(default_factory=list)
    signoff: SignoffData = field(default_factory=SignoffData)
    source_file: Optional[str] = None
    status: str = "success"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "meta": asdict(self.meta) if self.meta else {},
            "items": [asdict(item) for item in self.items] if self.items else [],
            "signoff": asdict(self.signoff) if self.signoff else {},
            "source_file": self.source_file,
            "status": self.status,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StructureAlterationSchema':
        """从字典创建实例"""
        meta = MetaData(**data.get('meta', {})) if data.get('meta') else MetaData()
        items = [ItemData(**item) for item in data.get('items', [])] if data.get('items') else []
        signoff = SignoffData(**data.get('signoff', {})) if data.get('signoff') else SignoffData()
        
        return cls(
            meta=meta,
            items=items,
            signoff=signoff,
            source_file=data.get('source_file'),
            status=data.get('status', 'success'),
            notes=data.get('notes')
        )


def get_json_schema() -> Dict[str, Any]:
    """
    获取JSON Schema定义,用于LLM结构化输出
    
    Returns:
        JSON Schema字典
    """
    return {
        "type": "object",
        "required": ["meta", "items"],
        "properties": {
            "meta": {
                "type": "object",
                "properties": {
                    "control_id": {"type": ["string", "null"], "description": "控制编号"},
                    "record_no": {"type": ["string", "null"], "description": "原始记录编号,格式如No:xxxxx"},
                    "instrument_id": {"type": ["string", "null"], "description": "仪器编号"},
                    "test_date": {"type": ["string", "null"], "description": "检测日期,格式YYYY-MM-DD"},
                    "house_name": {"type": ["string", "null"], "description": "房屋名称"}
                }
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "modification_location": {"type": ["string", "null"], "description": "拆改部位（完整提取该列所有文字）"},
                        "modification_description": {"type": ["string", "null"], "description": "拆改内容描述（整段原文，不改写）"},
                        "photo_no": {"type": ["string", "null"], "description": "照片编号"}
                    }
                }
            },
            "signoff": {
                "type": "object",
                "properties": {
                    "inspector": {"type": ["string", "null"], "description": "检查人"},
                    "recorder": {"type": ["string", "null"], "description": "记录人"},
                    "reviewer": {"type": ["string", "null"], "description": "审核人"}
                }
            },
            "notes": {"type": ["string", "null"], "description": "提取过程中的备注说明"}
        }
    }
