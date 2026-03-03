"""统一技能注册表：管理命令式和声明式 Skills"""

from enum import Enum
from pathlib import Path
from typing import Dict, Type, Optional, List, Any, Tuple

# 命令式 Skills
from collection.services.skills.ingest_skill import IngestSkill
from collection.services.skills.parse_skill import ParseSkill
from collection.services.skills.mapping_skill import MappingSkill
from collection.services.skills.validation_skill import ValidationSkill
# from services.skills.chapter_generation_skill import ChapterGenerationSkill  # 已弃用，使用声明式技能
from collection.services.skills.template_profile_skill import TemplateProfileSkill

# 声明式 Skills
from collection.services.declarative_skills.executor import DeclarativeSkillExecutor
from collection.services.declarative_skills.loader import SkillLoader


class SkillType(Enum):
    """技能类型"""
    IMPERATIVE = "imperative"  # 命令式
    DECLARATIVE = "declarative"  # 声明式


class SkillRegistry:
    """统一技能注册表"""

    def __init__(self):
        """初始化技能注册表"""
        # 命令式 Skills 注册表
        self._imperative_skills: Dict[str, Type] = {
            "ingest": IngestSkill,
            "parse": ParseSkill,
            "mapping": MappingSkill,
            "validation": ValidationSkill,
            # "chapter_generation": ChapterGenerationSkill,  # 已弃用，使用声明式技能
            "template_profile": TemplateProfileSkill,
        }

        # 声明式 Skills 执行器
        self._declarative_executor: Optional[DeclarativeSkillExecutor] = None
        self._declarative_skills: List[str] = []
        self._declarative_loader: Optional[SkillLoader] = None

    def initialize_declarative_skills(
        self, skills_base_path: Optional[Path] = None
    ) -> List[str]:
        """
        初始化声明式 Skills（扫描目录）
        
        Args:
            skills_base_path: Skills 基础目录路径
        
        Returns:
            发现的技能名称列表
        """
        if skills_base_path is None:
            # 默认路径优先尝试项目配置，或者是相对路径
            from config import settings
            skills_base_path = Path(settings.declarative_skills_path)

        if not skills_base_path.exists():
            # 尝试回退到默认位置（虽然 config 应该已经覆盖）
             skills_base_path = Path("backend/skills_library")

        if not skills_base_path.exists():
            return []

        # 创建执行器和加载器
        if self._declarative_executor is None:
            self._declarative_executor = DeclarativeSkillExecutor(
                skills_base_path=skills_base_path
            )
            self._declarative_loader = SkillLoader(skills_base_path)

        # 扫描声明式 Skills 目录
        self._declarative_skills = self._declarative_loader.list_available_skills()

        return self._declarative_skills

    def get_skill(
        self, skill_name: str
    ) -> Tuple[SkillType, Any]:
        """
        获取技能
        
        Args:
            skill_name: 技能名称
        
        Returns:
            (SkillType, skill_instance_or_executor)
        
        Raises:
            ValueError: 如果技能不存在
        """
        # 先检查命令式 Skills
        if skill_name in self._imperative_skills:
            skill_class = self._imperative_skills[skill_name]
            return SkillType.IMPERATIVE, skill_class

        # 再检查声明式 Skills
        if skill_name in self._declarative_skills:
            if self._declarative_executor is None:
                raise ValueError(
                    f"Declarative skills not initialized. "
                    f"Call initialize_declarative_skills() first."
                )
            return SkillType.DECLARATIVE, self._declarative_executor

        raise ValueError(
            f"Skill not found: {skill_name}. "
            f"Available imperative skills: {list(self._imperative_skills.keys())}, "
            f"Available declarative skills: {self._declarative_skills}"
        )

    def list_skills(self) -> Dict[str, List[str]]:
        """
        列出所有技能
        
        Returns:
            包含命令式和声明式技能名称的字典
        """
        return {
            "imperative": list(self._imperative_skills.keys()),
            "declarative": self._declarative_skills.copy(),
        }

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        获取技能信息
        
        Args:
            skill_name: 技能名称
        
        Returns:
            技能信息字典，如果不存在则返回 None
        """
        try:
            skill_type, skill_instance = self.get_skill(skill_name)

            info = {
                "name": skill_name,
                "type": skill_type.value,
            }

            if skill_type == SkillType.IMPERATIVE:
                info["class"] = skill_instance.__name__
            elif skill_type == SkillType.DECLARATIVE:
                # 尝试加载技能元数据
                if self._declarative_loader:
                    try:
                        metadata = self._declarative_loader.load_skill(skill_name)
                        info.update({
                            "display_name": metadata.display_name,
                            "description": metadata.description,
                            "version": metadata.version,
                            "has_script": metadata.script_path is not None,
                            "group": metadata.group,
                        })
                    except Exception:
                        pass

            return info

        except ValueError:
            return None
