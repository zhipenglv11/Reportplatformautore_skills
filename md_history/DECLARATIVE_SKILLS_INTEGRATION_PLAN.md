# 声明式 Skills 集成方案

## 📋 需求分析

### 当前状况
1. **现有命令式 Skills**（`backend/services/skills/`）
   - ParseSkill, MappingSkill, ValidationSkill 等
   - Python 类，直接代码执行
   - 适用于确定性流程

2. **待集成的声明式 Skills**（`D:\All_about_AI\projects\5_skills_create`）
   - `concrete-table-recognition`：混凝土表格识别
   - `notebooklm`：NotebookLM 查询
   - SKILL.md + fields.yaml + parse.py 格式

### 目标
- ✅ 混合架构：命令式和声明式 Skills 共存
- ✅ 模型无关：通过 LLM Gateway 支持多模型
- ✅ 统一管理：SkillRegistry 统一注册和发现
- ✅ 脚本执行：支持执行声明式 Skills 的脚本（如 parse.py）

---

## 🏗️ 架构设计

### 目录结构

```
backend/
├── services/
│   ├── skills/                    # 命令式 Skills（保持现有）
│   │   ├── ingest_skill.py
│   │   ├── parse_skill.py
│   │   └── ...
│   │
│   ├── declarative_skills/        # 新增：声明式 Skills 支持
│   │   ├── __init__.py
│   │   ├── loader.py              # SkillLoader：解析 SKILL.md 和 fields.yaml
│   │   ├── executor.py            # DeclarativeSkillExecutor：执行声明式 Skills
│   │   ├── script_runner.py       # ScriptRunner：执行脚本（parse.py 等）
│   │   └── models.py              # 数据模型（SkillMetadata 等）
│   │
│   ├── skill_registry/            # 新增：统一技能注册表
│   │   ├── __init__.py
│   │   ├── registry.py            # SkillRegistry：统一管理所有 Skills
│   │   └── types.py               # 技能类型定义
│   │
│   └── llm_gateway/               # 现有：LLM Gateway（已支持多模型）
│       └── gateway.py
│
└── declarative_skills/            # 声明式 Skills 存储目录（可配置）
    ├── concrete-table-recognition/
    │   ├── SKILL.md
    │   ├── fields.yaml
    │   └── parse.py
    └── notebooklm/
        ├── SKILL.md
        └── ...
```

---

## 🔧 核心组件实现

### 1. SkillLoader（技能加载器）

**功能**：解析 SKILL.md 和 fields.yaml，加载技能元数据

```python
# backend/services/declarative_skills/loader.py
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import re

class SkillLoader:
    """加载声明式 Skills（解析 SKILL.md 和 fields.yaml）"""
    
    def __init__(self, skills_base_path: Optional[Path] = None):
        self.skills_base_path = skills_base_path or Path("declarative_skills")
    
    def load_skill(self, skill_name: str) -> 'SkillMetadata':
        """加载指定技能"""
        skill_dir = self.skills_base_path / skill_name
        if not skill_dir.exists():
            raise ValueError(f"Skill not found: {skill_name}")
        
        # 1. 解析 SKILL.md
        skill_md_path = skill_dir / "SKILL.md"
        if not skill_md_path.exists():
            raise ValueError(f"SKILL.md not found in {skill_name}")
        
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
            version=metadata.get("version", "1.0.0"),
            content=metadata.get("content", ""),  # SKILL.md 的完整内容
            fields=fields,
            script_path=script_path,
            skill_dir=skill_dir,
        )
    
    def _parse_skill_md(self, skill_md_path: Path) -> Dict[str, Any]:
        """解析 SKILL.md 的 YAML frontmatter"""
        content = skill_md_path.read_text(encoding="utf-8")
        
        # 提取 YAML frontmatter
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        metadata = {}
        if match:
            yaml_str = match.group(1)
            body = match.group(2)
            metadata = yaml.safe_load(yaml_str) or {}
            metadata["content"] = body
        else:
            metadata["content"] = content
        
        return metadata
    
    def _load_fields(self, fields_path: Path) -> Dict[str, Any]:
        """加载 fields.yaml"""
        with open(fields_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
```

### 2. SkillMetadata（技能元数据模型）

```python
# backend/services/declarative_skills/models.py
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

@dataclass
class SkillMetadata:
    """声明式 Skill 的元数据"""
    name: str
    description: str
    version: str
    content: str  # SKILL.md 的完整内容
    fields: Dict[str, Any]  # fields.yaml 的内容
    script_path: Optional[Path]  # 脚本路径（如 parse.py）
    skill_dir: Path  # 技能目录
```

### 3. ScriptRunner（脚本执行器）

**功能**：执行声明式 Skills 的脚本（如 parse.py）

```python
# backend/services/declarative_skills/script_runner.py
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys

class ScriptRunner:
    """执行声明式 Skills 的脚本"""
    
    def __init__(self, skill_dir: Path):
        self.skill_dir = skill_dir
    
    def run_script(
        self,
        script_name: str = "parse.py",
        args: Optional[list] = None,
        input_data: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        执行脚本
        
        Args:
            script_name: 脚本文件名（如 "parse.py"）
            args: 命令行参数
            input_data: 输入数据（通过 stdin 传递）
            env: 环境变量
        
        Returns:
            执行结果
        """
        script_path = self.skill_dir / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # 构建命令
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        # 构建环境变量
        script_env = dict(os.environ)
        if env:
            script_env.update(env)
        
        # 执行脚本
        try:
            process = subprocess.run(
                cmd,
                cwd=str(self.skill_dir),
                input=json.dumps(input_data) if input_data else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env=script_env,
                timeout=300,  # 5分钟超时
            )
            
            # 解析输出
            stdout = process.stdout
            stderr = process.stderr
            
            # 尝试解析 JSON 输出
            try:
                output = json.loads(stdout)
            except json.JSONDecodeError:
                output = {"stdout": stdout, "stderr": stderr}
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": output,
                "stderr": stderr,
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
```

### 4. DeclarativeSkillExecutor（声明式技能执行器）

**功能**：执行声明式 Skills，支持 LLM 调用和脚本执行

```python
# backend/services/declarative_skills/executor.py
from typing import Dict, Any, Optional
from pathlib import Path

from services.llm_gateway.gateway import LLMGateway
from services.declarative_skills.loader import SkillLoader
from services.declarative_skills.script_runner import ScriptRunner
from services.declarative_skills.models import SkillMetadata
from config import settings

class DeclarativeSkillExecutor:
    """执行声明式 Skills"""
    
    def __init__(
        self,
        llm_gateway: Optional[LLMGateway] = None,
        skills_base_path: Optional[Path] = None,
    ):
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
            **kwargs: 其他参数（如 provider, model 等）
        
        Returns:
            执行结果
        """
        # 1. 加载 Skill
        skill = self.loader.load_skill(skill_name)
        
        # 2. 构建 system prompt
        system_prompt = self._build_system_prompt(skill)
        
        # 3. 如果需要使用 LLM
        llm_response = None
        if use_llm:
            llm_response = await self._execute_with_llm(
                skill, user_input, context, system_prompt, **kwargs
            )
        
        # 4. 如果需要执行脚本
        script_result = None
        if use_script and skill.script_path:
            script_runner = ScriptRunner(skill.skill_dir)
            script_result = script_runner.run_script(
                script_name=skill.script_path.name,
                args=kwargs.get("script_args", []),
                input_data={
                    "user_input": user_input,
                    "llm_response": llm_response,
                    "context": context or {},
                },
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
        """构建 system prompt"""
        prompt_parts = [
            f"# Skill: {skill.name}",
            f"Version: {skill.version}",
            "",
            f"## Description",
            skill.description,
            "",
            f"## Instructions",
            skill.content,
        ]
        
        # 添加字段定义
        if skill.fields:
            prompt_parts.append("")
            prompt_parts.append("## Available Fields")
            prompt_parts.append(self._format_fields(skill.fields))
        
        return "\n".join(prompt_parts)
    
    def _format_fields(self, fields: Dict[str, Any]) -> str:
        """格式化字段定义"""
        # 简化实现，实际可以更详细
        return yaml.dump(fields, allow_unicode=True, default_flow_style=False)
    
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
        """使用 LLM 执行"""
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
        )
        
        return response
```

### 5. SkillRegistry（统一技能注册表）

**功能**：统一管理命令式和声明式 Skills

```python
# backend/services/skill_registry/registry.py
from typing import Dict, Type, Optional, List
from enum import Enum

# 命令式 Skills
from services.skills.ingest_skill import IngestSkill
from services.skills.parse_skill import ParseSkill
from services.skills.mapping_skill import MappingSkill
from services.skills.validation_skill import ValidationSkill
from services.skills.chapter_generation_skill import ChapterGenerationSkill
from services.skills.template_profile_skill import TemplateProfileSkill

# 声明式 Skills
from services.declarative_skills.executor import DeclarativeSkillExecutor

class SkillType(Enum):
    """技能类型"""
    IMPERATIVE = "imperative"  # 命令式
    DECLARATIVE = "declarative"  # 声明式

class SkillRegistry:
    """统一技能注册表"""
    
    def __init__(self):
        # 命令式 Skills 注册表
        self._imperative_skills: Dict[str, Type] = {
            "ingest": IngestSkill,
            "parse": ParseSkill,
            "mapping": MappingSkill,
            "validation": ValidationSkill,
            "chapter_generation": ChapterGenerationSkill,
            "template_profile": TemplateProfileSkill,
        }
        
        # 声明式 Skills 执行器
        self._declarative_executor: Optional[DeclarativeSkillExecutor] = None
        self._declarative_skills: List[str] = []
    
    def initialize_declarative_skills(self, skills_base_path: Optional[Path] = None):
        """初始化声明式 Skills（扫描目录）"""
        from pathlib import Path
        from services.declarative_skills.loader import SkillLoader
        
        if self._declarative_executor is None:
            self._declarative_executor = DeclarativeSkillExecutor(
                skills_base_path=skills_base_path
            )
        
        # 扫描声明式 Skills 目录
        base_path = skills_base_path or Path("declarative_skills")
        if base_path.exists():
            for skill_dir in base_path.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    self._declarative_skills.append(skill_dir.name)
    
    def get_skill(self, skill_name: str) -> tuple[SkillType, Any]:
        """
        获取技能
        
        Returns:
            (SkillType, skill_instance_or_executor)
        """
        # 先检查命令式 Skills
        if skill_name in self._imperative_skills:
            skill_class = self._imperative_skills[skill_name]
            return SkillType.IMPERATIVE, skill_class
        
        # 再检查声明式 Skills
        if skill_name in self._declarative_skills:
            return SkillType.DECLARATIVE, self._declarative_executor
        
        raise ValueError(f"Skill not found: {skill_name}")
    
    def list_skills(self) -> Dict[str, List[str]]:
        """列出所有技能"""
        return {
            "imperative": list(self._imperative_skills.keys()),
            "declarative": self._declarative_skills,
        }
```

---

## 🔌 API 集成

### 新增 API 路由

```python
# backend/api/declarative_skill_routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.skill_registry.registry import SkillRegistry

router = APIRouter()
skill_registry = SkillRegistry()

# 初始化声明式 Skills
skill_registry.initialize_declarative_skills(
    skills_base_path=Path("D:/All_about_AI/projects/5_skills_create")
)

class ExecuteDeclarativeSkillRequest(BaseModel):
    skill_name: str
    user_input: str
    context: Optional[Dict[str, Any]] = None
    use_llm: bool = True
    use_script: bool = True
    provider: Optional[str] = None
    model: Optional[str] = None

@router.post("/skill/execute")
async def execute_skill(request: ExecuteDeclarativeSkillRequest):
    """执行声明式 Skill"""
    try:
        skill_type, skill_instance = skill_registry.get_skill(request.skill_name)
        
        if skill_type == SkillType.DECLARATIVE:
            result = await skill_instance.execute(
                skill_name=request.skill_name,
                user_input=request.user_input,
                context=request.context,
                use_llm=request.use_llm,
                use_script=request.use_script,
                provider=request.provider,
                model=request.model,
            )
            return result
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Skill {request.skill_name} is imperative, use direct API"
            )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/skills/list")
async def list_skills():
    """列出所有技能"""
    return skill_registry.list_skills()

@router.post("/skill/concrete-table-recognition")
async def concrete_table_recognition(
    file: UploadFile = File(...),
    format: str = Form("json"),
    output_dir: Optional[str] = Form(None),
):
    """混凝土表格识别（专用接口）"""
    # 1. 保存文件到临时目录
    import tempfile
    import shutil
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # 2. 执行声明式 Skill
        skill_type, executor = skill_registry.get_skill("concrete-table-recognition")
        
        script_args = [tmp_path, "--format", format]
        if output_dir:
            script_args.extend(["--output-dir", output_dir])
        
        result = await executor.execute(
            skill_name="concrete-table-recognition",
            user_input=f"处理文件: {file.filename}",
            use_llm=False,  # 直接执行脚本
            use_script=True,
            script_args=script_args,
        )
        
        return result
    
    finally:
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)
```

---

## ⚙️ 配置更新

```python
# backend/config.py
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 新增：声明式 Skills 配置
    declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
    enable_declarative_skills: bool = True
```

---

## 📝 使用示例

### 1. 在代码中使用

```python
from services.skill_registry.registry import SkillRegistry, SkillType

registry = SkillRegistry()
registry.initialize_declarative_skills()

# 执行声明式 Skill
skill_type, executor = registry.get_skill("concrete-table-recognition")
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="处理这个PDF文件",
    context={"file_path": "/path/to/file.pdf"},
    use_script=True,
)
```

### 2. 通过 API 调用

```bash
# 执行混凝土表格识别
curl -X POST http://localhost:8000/api/skill/concrete-table-recognition \
  -F "file=@table.pdf" \
  -F "format=json"

# 通用 Skill 执行接口
curl -X POST http://localhost:8000/api/skill/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "concrete-table-recognition",
    "user_input": "处理这个PDF文件",
    "use_script": true
  }'
```

---

## 🎯 实施步骤

1. ✅ **创建目录结构**
   - `backend/services/declarative_skills/`
   - `backend/services/skill_registry/`

2. ✅ **实现核心组件**
   - SkillLoader
   - ScriptRunner
   - DeclarativeSkillExecutor
   - SkillRegistry

3. ✅ **添加 API 路由**
   - `/api/skill/execute`
   - `/api/skill/concrete-table-recognition`
   - `/api/skills/list`

4. ✅ **测试集成**
   - 测试 concrete-table-recognition skill
   - 测试脚本执行
   - 测试 LLM 调用

5. ✅ **文档更新**
   - API 文档
   - 使用指南

---

## ⚠️ 注意事项

1. **路径配置**：声明式 Skills 路径需要可配置（可通过环境变量或配置文件）
2. **脚本依赖**：确保脚本的依赖已安装（如 concrete-table-recognition 的 requirements.txt）
3. **环境变量**：脚本可能需要环境变量（如 API keys），需要在 ScriptRunner 中传递
4. **错误处理**：脚本执行失败时的错误处理
5. **安全性**：脚本执行的沙箱隔离（如果需要）
