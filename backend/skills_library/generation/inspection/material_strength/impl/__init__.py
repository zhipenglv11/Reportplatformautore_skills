"""
Material Strength - Parent Skill Implementation
父skill实现模块
"""

from .assemble import (
    assemble_material_strength,
    detect_available_materials,
    call_subskill
)

__all__ = [
    "assemble_material_strength",
    "detect_available_materials", 
    "call_subskill"
]
