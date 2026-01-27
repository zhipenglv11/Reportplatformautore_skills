# -*- coding: utf-8 -*-
"""技能加载器：解析 SKILL.md 和 fields.yaml"""

import re
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from .models import SkillMetadata


class SkillLoader:
    """加载声明式 Skills（解析 SKILL.md 和 fields.yaml）"""

    def __init__(self, skills_base_path: Optional[Path] = None):
        """
        初始化技能加载器
        
        Args:
            skills_base_path: Skills 基础目录路径，默认为 None（需要外部指定）
        """
        self.skills_base_path = skills_base_path
        self._skill_index: Dict[str, Path] = {}

    def load_skill(self, skill_name: str) -> SkillMetadata:
        """
        加载指定技能
        
        Args:
            skill_name: 技能名称（目录名）
        
        Returns:
            SkillMetadata: 技能元数据
        
        Raises:
            ValueError: 如果技能不存在或缺少必要文件
        """
        if not self.skills_base_path:
            raise ValueError("skills_base_path is not set")

        skill_dir = self._resolve_skill_dir(skill_name)
        if not skill_dir:
            raise ValueError(f"Skill not found: {skill_name}")

        # 1. 解析 SKILL.md
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            raise ValueError(f"SKILL.md not found in {skill_name} (path: {skill_md_path})")

        metadata = self._parse_skill_md(skill_md_path)

        # 2. 加载 fields.yaml（可选）
        fields = {}
        fields_path = skill_dir / "fields.yaml"
        if fields_path.exists():
            fields = self._load_fields(fields_path)

        # 3. 检查脚本文件
        script_path = None
        if (skill_dir / "parse.py").exists():
            script_path = skill_dir / "parse.py"

        return SkillMetadata(
            name=metadata.get("name", skill_name),
            description=metadata.get("description", ""),
            display_name=metadata.get("display_name"),
            version=metadata.get("version", "1.0.0"),
            content=metadata.get("content", ""),  # SKILL.md 的完整内容
            fields=fields,
            script_path=script_path,
            skill_dir=skill_dir,
            group=self._get_group_for_dir(skill_dir),
        )

    def _parse_skill_md(self, skill_md_path: Path) -> Dict[str, Any]:
        """
        解析 SKILL.md 的 YAML frontmatter
        
        Args:
            skill_md_path: SKILL.md 文件路径
        
        Returns:
            包含元数据和内容的字典
        """
        content = skill_md_path.read_text(encoding="utf-8-sig")

        # 提取 YAML frontmatter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        metadata = {}
        if match:
            yaml_str = match.group(1)
            body = match.group(2)
            try:
                metadata = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse YAML frontmatter in {skill_md_path}: {e}")
            metadata["content"] = body
        else:
            # 没有 frontmatter，整个文件作为内容
            metadata["content"] = content

        return metadata

    def _load_fields(self, fields_path: Path) -> Dict[str, Any]:
        """
        加载 fields.yaml
        
        Args:
            fields_path: fields.yaml 文件路径
        
        Returns:
            字段定义字典
        """
        try:
            with open(fields_path, "r", encoding="utf-8-sig") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse fields.yaml: {e}")

    def list_available_skills(self) -> list[str]:
        """
        列出所有可用的声明式 Skills
        
        Returns:
            技能名称列表
        """
        if not self.skills_base_path or not self.skills_base_path.exists():
            return []

        self._build_skill_index()
        return sorted(self._skill_index.keys())

    def _build_skill_index(self) -> None:
        if self._skill_index:
            return
        if not self.skills_base_path or not self.skills_base_path.exists():
            return

        for skill_md in self.skills_base_path.rglob("SKILL.md"):
            skill_dir = skill_md.parent
            skill_name = skill_dir.name
            if skill_name in self._skill_index:
                raise ValueError(
                    f"Duplicate skill name detected: {skill_name} "
                    f"({self._skill_index[skill_name]} vs {skill_dir})"
                )
            self._skill_index[skill_name] = skill_dir

    def _get_group_for_dir(self, skill_dir: Path) -> Optional[str]:
        if not self.skills_base_path:
            return None
        try:
            relative = skill_dir.relative_to(self.skills_base_path)
        except ValueError:
            return None
        if len(relative.parts) <= 1:
            return None
        return relative.parts[0]

    def _resolve_skill_dir(self, skill_name: str) -> Optional[Path]:
        if not skill_name:
            return None
        self._build_skill_index()
        return self._skill_index.get(skill_name)
