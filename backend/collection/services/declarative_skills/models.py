# -*- coding: utf-8 -*-
"""声明式 Skill 的数据模型"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class SkillMetadata:
    """声明式 Skill 的元数据"""
    name: str
    description: str
    display_name: Optional[str]
    version: str
    content: str  # SKILL.md 的完整内容
    fields: Dict[str, Any]  # fields.yaml 的内容
    script_path: Optional[Path]  # 脚本路径（如 parse.py）
    skill_dir: Path  # 技能目录
    group: Optional[str] = None  # 所属功能分组（基于目录）
