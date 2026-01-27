"""
Skills module for structure damage and alterations extraction
结构损伤及拆改检查数据抽取技能模块
"""

from .extractor import StructureAlterationExtractor
from .schema import StructureAlterationSchema
from .prompt import get_system_prompt, get_extraction_prompt

__all__ = [
    'StructureAlterationExtractor',
    'StructureAlterationSchema',
    'get_system_prompt',
    'get_extraction_prompt'
]
