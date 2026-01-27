# -*- coding: utf-8 -*-
"""声明式技能执行器"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from config import settings
from services.llm_gateway.gateway import LLMGateway
from .loader import SkillLoader
from .script_runner import ScriptRunner
from .models import SkillMetadata


class DeclarativeSkillExecutor:
    """执行声明式 Skills"""

    def __init__(
        self,
        llm_gateway: Optional[LLMGateway] = None,
        skills_base_path: Optional[Path] = None,
    ):
        """
        初始化声明式技能执行器
        
        Args:
            llm_gateway: LLM Gateway 实例，如果为 None 则创建新实例
            skills_base_path: Skills 基础目录路径
        """
        self.llm_gateway = llm_gateway or LLMGateway()
        self.loader = SkillLoader(skills_base_path)

    async def execute(
        self,
        skill_name: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
        use_script: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行声明式 Skill
        
        Args:
            skill_name: 技能名称
            user_input: 用户输入
            context: 上下文数据
            use_llm: 是否使用 LLM
            use_script: 是否执行脚本
            **kwargs: 其他参数
                - provider: LLM provider
                - model: LLM model
                - temperature: LLM temperature
                - script_args: 脚本参数列表
                - script_name: 脚本文件名（默认 "parse.py"）
                - script_timeout: 脚本超时时间（秒）
        
        Returns:
            执行结果字典
        """
        # 1. 加载 Skill
        skill = self.loader.load_skill(skill_name)

        # 2. 如果需要使用 LLM
        llm_response = None
        if use_llm:
            system_prompt = self._build_system_prompt(skill)
            llm_response = await self._execute_with_llm(
                skill, user_input, context, system_prompt, **kwargs
            )

        # 3. 如果需要执行脚本
        script_result = None
        if use_script and skill.script_path:
            script_runner = ScriptRunner(skill.skill_dir)
            script_name = kwargs.get("script_name", skill.script_path.name)
            script_args = kwargs.get("script_args", [])
            script_timeout = kwargs.get("script_timeout", 300)
            script_env = kwargs.get("env", {})

            script_result = script_runner.run_script(
                script_name=script_name,
                args=script_args,
                input_data={
                    "user_input": user_input,
                    "llm_response": llm_response,
                    "context": context or {},
                },
                env=script_env,
                timeout=script_timeout,
            )

        return {
            "skill_name": skill_name,
            "llm_response": llm_response,
            "script_result": script_result,
            "metadata": {
                "name": skill.name,
                "description": skill.description,
                "version": skill.version,
            },
        }

    def _build_system_prompt(self, skill: SkillMetadata) -> str:
        """
        构建 system prompt
        
        Args:
            skill: 技能元数据
        
        Returns:
            system prompt 字符串
        """
        prompt_parts = [
            f"# Skill: {skill.name}",
            f"Version: {skill.version}",
            "",
            "## Description",
            skill.description,
            "",
            "## Instructions",
            skill.content,
        ]

        # 添加字段定义
        if skill.fields:
            prompt_parts.append("")
            prompt_parts.append("## Available Fields")
            prompt_parts.append(self._format_fields(skill.fields))

        return "\n".join(prompt_parts)

    def _format_fields(self, fields: Dict[str, Any]) -> str:
        """
        格式化字段定义
        
        Args:
            fields: 字段定义字典
        
        Returns:
            格式化后的字符串
        """
        try:
            return yaml.dump(fields, allow_unicode=True, default_flow_style=False)
        except Exception:
            return json.dumps(fields, ensure_ascii=False, indent=2)

    async def _execute_with_llm(
        self,
        skill: SkillMetadata,
        user_input: str,
        context: Optional[Dict[str, Any]],
        system_prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        使用 LLM 执行
        
        Args:
            skill: 技能元数据
            user_input: 用户输入
            context: 上下文数据
            system_prompt: system prompt
            provider: LLM provider
            model: LLM model
            **kwargs: 其他参数
        
        Returns:
            LLM 响应字典
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context: {json.dumps(context, ensure_ascii=False)}",
            })

        response = await self.llm_gateway.chat_completion(
            provider=provider or settings.llm_provider,
            model=model or settings.llm_model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens"),
        )

        return response
