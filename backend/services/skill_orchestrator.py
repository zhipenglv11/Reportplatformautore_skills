"""技能编排器：智能识别文件类型并路由到对应技能"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from services.llm_gateway.gateway import LLMGateway
from services.skill_registry.registry import SkillRegistry, SkillType
from config import settings


@dataclass
class FileClassification:
    """文件分类结果"""
    file_name: str
    file_type: str  # 文件类型：concrete, mortar, brick, software_result, etc.
    skill_name: Optional[str]  # 对应的技能名称
    confidence: float  # 识别置信度
    reasoning: str  # 识别理由


@dataclass
class OrchestrationResult:
    """编排执行结果"""
    file_name: str
    classification: FileClassification
    skill_result: Optional[Dict[str, Any]]
    success: bool
    error: Optional[str] = None


class SkillOrchestrator:
    """技能编排器：智能识别文件并路由到对应技能"""
    
    def __init__(
        self,
        llm_gateway: Optional[LLMGateway] = None,
        skill_registry: Optional[SkillRegistry] = None,
    ):
        """
        初始化技能编排器
        
        Args:
            llm_gateway: LLM Gateway 实例
            skill_registry: 技能注册表实例
        """
        self.llm_gateway = llm_gateway or LLMGateway()
        self.skill_registry = skill_registry or SkillRegistry()
        
        # 文件类型到技能的映射规则
        self.file_type_to_skill = {
            "concrete": "concrete-table-recognition",
            "mortar": "concrete-table-recognition",  # 可以使用相同的技能
            "brick": "concrete-table-recognition",  # 可以使用相同的技能
            "software_result": "concrete-table-recognition",  # 或创建新的技能
        }
        
        # 技能描述映射（用于 LLM 识别）
        self.skill_descriptions = {
            "concrete-table-recognition": "识别和提取混凝土、砂浆、砖强度等检测表格数据",
            # 可以添加更多技能描述
        }
    
    async def classify_file(
        self,
        file_path: Path,
        file_name: str,
        file_content_preview: Optional[str] = None,
    ) -> FileClassification:
        """
        使用 LLM 识别文件类型
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            file_content_preview: 文件内容预览（可选，用于文本文件）
        
        Returns:
            FileClassification: 文件分类结果
        """
        # 构建识别 prompt
        system_prompt = """你是一个专业的文件类型识别助手。你的任务是识别上传的文件类型，并确定应该使用哪个技能来处理它。

可用的技能：
1. concrete-table-recognition: 用于识别和提取混凝土、砂浆、砖强度等检测表格数据

文件类型包括：
- concrete: 混凝土强度检测表（如回弹检测记录表、强度结果表等）
- mortar: 砂浆强度检测表
- brick: 砖强度检测表
- software_result: 软件计算结果表
- other: 其他类型

请根据文件名和内容（如果有）识别文件类型，并返回 JSON 格式：
{
  "file_type": "concrete|mortar|brick|software_result|other",
  "skill_name": "concrete-table-recognition|null",
  "confidence": 0.0-1.0,
  "reasoning": "识别理由"
}"""

        user_prompt = f"""请识别以下文件：

文件名: {file_name}
文件路径: {file_path}

"""
        
        if file_content_preview:
            user_prompt += f"文件内容预览（前500字符）:\n{file_content_preview[:500]}\n"
        
        user_prompt += "\n请返回 JSON 格式的识别结果。"

        try:
            # 调用 LLM 进行识别
            response = await self.llm_gateway.chat_completion(
                provider=settings.llm_provider,
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # 降低温度以获得更确定的结果
                response_format={"type": "json_object"},
            )
            
            # 解析响应
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            result = json.loads(content)
            
            file_type = result.get("file_type", "other")
            skill_name = result.get("skill_name")
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")
            
            # 如果没有指定技能，根据文件类型查找
            if not skill_name and file_type in self.file_type_to_skill:
                skill_name = self.file_type_to_skill[file_type]
            
            return FileClassification(
                file_name=file_name,
                file_type=file_type,
                skill_name=skill_name,
                confidence=confidence,
                reasoning=reasoning,
            )
            
        except Exception as e:
            # 如果 LLM 识别失败，使用规则匹配
            return self._classify_by_rules(file_name)
    
    def _classify_by_rules(self, file_name: str) -> FileClassification:
        """
        使用规则匹配识别文件类型（LLM 失败时的后备方案）
        
        Args:
            file_name: 文件名
        
        Returns:
            FileClassification: 文件分类结果
        """
        file_name_lower = file_name.lower()
        
        # 规则匹配
        if any(keyword in file_name_lower for keyword in ["混凝土", "concrete", "回弹", "rebound"]):
            file_type = "concrete"
            skill_name = "concrete-table-recognition"
            confidence = 0.8
            reasoning = "文件名包含混凝土相关关键词"
        elif any(keyword in file_name_lower for keyword in ["砂浆", "mortar"]):
            file_type = "mortar"
            skill_name = "concrete-table-recognition"
            confidence = 0.8
            reasoning = "文件名包含砂浆相关关键词"
        elif any(keyword in file_name_lower for keyword in ["砖", "brick"]):
            file_type = "brick"
            skill_name = "concrete-table-recognition"
            confidence = 0.8
            reasoning = "文件名包含砖相关关键词"
        elif any(keyword in file_name_lower for keyword in ["软件", "software", "计算", "result"]):
            file_type = "software_result"
            skill_name = "concrete-table-recognition"
            confidence = 0.7
            reasoning = "文件名包含软件计算结果相关关键词"
        else:
            file_type = "other"
            skill_name = None
            confidence = 0.3
            reasoning = "无法识别文件类型，使用默认规则"
        
        return FileClassification(
            file_name=file_name,
            file_type=file_type,
            skill_name=skill_name,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    async def orchestrate_files(
        self,
        files: List[Tuple[Path, str]],  # [(file_path, file_name), ...]
        project_id: str,
        node_id: str,
        persist_result: bool = True,
    ) -> List[OrchestrationResult]:
        """
        编排多个文件：识别类型并执行对应技能
        
        Args:
            files: 文件列表，每个元素是 (file_path, file_name)
            project_id: 项目ID
            node_id: 节点ID
            persist_result: 是否提交到数据库
        
        Returns:
            List[OrchestrationResult]: 执行结果列表
        """
        results = []
        
        # 步骤1：识别所有文件的类型
        classifications = []
        for file_path, file_name in files:
            try:
                # 尝试读取文件预览（如果是文本文件）
                file_content_preview = None
                try:
                    if file_path.suffix.lower() in ['.txt', '.csv']:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        file_content_preview = content[:500]
                except:
                    pass
                
                classification = await self.classify_file(
                    file_path=file_path,
                    file_name=file_name,
                    file_content_preview=file_content_preview,
                )
                classifications.append((file_path, file_name, classification))
            except Exception as e:
                # 识别失败，使用规则匹配
                classification = self._classify_by_rules(file_name)
                classifications.append((file_path, file_name, classification))
        
        # 步骤2：按技能分组执行
        skill_groups: Dict[str, List[Tuple[Path, str, FileClassification]]] = {}
        for file_path, file_name, classification in classifications:
            skill_name = classification.skill_name
            if skill_name:
                if skill_name not in skill_groups:
                    skill_groups[skill_name] = []
                skill_groups[skill_name].append((file_path, file_name, classification))
            else:
                # 没有匹配的技能，记录为失败
                results.append(OrchestrationResult(
                    file_name=file_name,
                    classification=classification,
                    skill_result=None,
                    success=False,
                    error=f"未找到匹配的技能，文件类型: {classification.file_type}",
                ))
        
        # 步骤3：执行每个技能组
        for skill_name, file_group in skill_groups.items():
            for file_path, file_name, classification in file_group:
                try:
                    # 获取技能执行器
                    skill_type, executor = self.skill_registry.get_skill(skill_name)
                    
                    if skill_type != SkillType.DECLARATIVE:
                        results.append(OrchestrationResult(
                            file_name=file_name,
                            classification=classification,
                            skill_result=None,
                            success=False,
                            error=f"技能 {skill_name} 不是声明式技能",
                        ))
                        continue
                    
                    # 执行技能
                    script_args = [str(file_path), "--format", "json"]
                    skill_result = await executor.execute(
                        skill_name=skill_name,
                        user_input=f"处理文件: {file_name}",
                        use_llm=False,
                        use_script=True,
                        script_args=script_args,
                    )
                    
                    results.append(OrchestrationResult(
                        file_name=file_name,
                        classification=classification,
                        skill_result=skill_result,
                        success=True,
                    ))
                        
                except Exception as e:
                    results.append(OrchestrationResult(
                        file_name=file_name,
                        classification=classification,
                        skill_result=None,
                        success=False,
                        error=str(e),
                    ))
        
        return results
