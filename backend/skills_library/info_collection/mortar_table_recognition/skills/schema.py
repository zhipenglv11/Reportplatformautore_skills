"""
Mortar Strength Schema Definition
砂浆强度检测数据模式定义

Defines the expected output schema for mortar strength inspection data.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class MortarMetaSchema:
    """
    Schema for table header/meta information.
    表头字段模式定义
    """
    table_id: Optional[str] = None  # 控制编号(表格ID) - 左上角
    record_no: Optional[str] = None  # 原始记录编号 - 右上角 No: xxxxx
    test_date: Optional[str] = None  # 检测日期 - YYYY-MM-DD 或原字符串
    instrument_model: Optional[str] = None  # 仪器型号


@dataclass
class MortarRowSchema:
    """
    Schema for individual row data.
    单行数据模式定义
    """
    seq: Optional[int] = None  # 序号
    test_location: Optional[str] = None  # 检测部位(第一列)
    converted_strength_mpa: Optional[float] = None  # 砂浆抗压强度换算值(倒数第二列)
    estimated_strength_mpa: Optional[float] = None  # 单个构件强度推定值(倒数第一列)


@dataclass
class MortarSchema:
    """
    Complete schema for mortar strength inspection data.
    完整的砂浆强度检测数据模式
    """
    meta: Optional[MortarMetaSchema] = None  # 表头信息
    rows: List[MortarRowSchema] = field(default_factory=list)  # 行数据
    notes: Optional[str] = None  # 备注信息
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None
        }
    
    @classmethod
    def get_field_names(cls) -> List[str]:
        """Get list of all field names."""
        return ['meta', 'rows', 'notes']
    
    @classmethod
    def get_meta_field_names(cls) -> List[str]:
        """Get list of meta field names."""
        return list(MortarMetaSchema.__annotations__.keys())
    
    @classmethod
    def get_row_field_names(cls) -> List[str]:
        """Get list of row field names."""
        return list(MortarRowSchema.__annotations__.keys())
    
    @classmethod
    def get_required_fields(cls) -> List[str]:
        """
        Get list of required field names.
        """
        return [
            'meta.table_id',
            'meta.record_no',
            'meta.test_date',
            'rows[].test_location'
        ]
    
    @classmethod
    def get_field_descriptions(cls) -> Dict[str, str]:
        """
        Get field descriptions for prompt generation.
        """
        return {
            # Meta fields
            "meta.table_id": "控制编号(表格ID) - 位于左上角,示例:KJQR-056-206",
            "meta.record_no": "原始记录编号 - 位于右上角 No: xxxxx,示例:2500108",
            "meta.test_date": "检测日期 - 格式YYYY-MM-DD,示例:2023-02-26,无法规范化则保留原字符串",
            "meta.instrument_model": "仪器型号 - 示例:SJY-800B",
            
            # Row fields
            "rows[].seq": "序号 - 表格序号列,识别不到允许null,不自动补号",
            "rows[].test_location": "检测部位 - 第一列,示例:一层墙 19×D-F 轴,去首尾空格、压缩连续空格",
            "rows[].converted_strength_mpa": "砂浆抗压强度换算值 - 倒数第二列,单位MPa,按原记录数值保留位数,空/占位符输出null",
            "rows[].estimated_strength_mpa": "单个构件强度推定值 - 倒数第一列,单位MPa,按原记录数值保留位数,空/占位符输出null",
            
            # Other
            "notes": "备注信息 - 记录任何歧义、不确定或特殊情况"
        }
