# Skills 架构对比分析：Claude Skills vs 项目现有 Skills

## 📊 总体对比

| 维度 | Claude Skills | 项目现有 Skills |
|------|---------------|----------------|
| **定义方式** | 声明式（SKILL.md + YAML） | 命令式（Python 类） |
| **执行机制** | LLM 解释执行（通过 system prompt） | 代码直接执行（Python 函数） |
| **元数据存储** | SKILL.md（YAML frontmatter） | 代码注释/docstring |
| **字段定义** | fields.yaml | 代码中的参数和返回值类型 |
| **脚本支持** | 可执行脚本（如 parse.py） | 直接包含在 Python 类中 |
| **加载机制** | SkillLoader（解析文件） | Python import（直接导入） |
| **执行引擎** | SkillExecutor（构建 prompt + 调用 LLM） | 直接调用 execute() 方法 |

---

## 🔍 详细对比

### 1. **定义方式**

#### Claude Skills（声明式）
```
skill_directory/
├── SKILL.md          # 技能描述和指令（含 YAML frontmatter）
├── fields.yaml       # 字段定义
└── parse.py          # 可选：执行脚本
```

**SKILL.md 示例结构**：
```markdown
---
name: pdf_parser
description: 解析PDF文件的表格数据
version: 1.0.0
---

# PDF 解析技能

本技能用于解析PDF文件中的表格数据...

## 使用方法
...
```

#### 项目现有 Skills（命令式）
```python
# backend/services/skills/parse_skill.py
class ParseSkill:
    """Vision-first parse: convert to page images and optional LLM call."""
    
    def __init__(self, llm_gateway: Optional[LLMGateway] = None) -> None:
        self.llm_gateway = llm_gateway
    
    async def execute(
        self,
        ingest_result: Dict[str, str],
        use_llm: bool = False,
        prompt: Optional[str] = None,
    ) -> Dict[str, object]:
        # 具体实现代码
        ...
```

**关键区别**：
- ✅ **Claude Skills**：通过文档描述技能，LLM 理解并执行
- ✅ **项目 Skills**：通过代码实现技能，Python 解释器执行

---

### 2. **执行机制**

#### Claude Skills 执行流程
```python
# 伪代码示例
class SkillExecutor:
    def execute(self, skill_name, user_input):
        # 1. 加载 Skill 定义
        skill = self.loader.load_skill(skill_name)
        
        # 2. 构建 System Prompt
        system_prompt = f"""
        # Skill: {skill.name}
        {skill.description}
        
        ## Available Fields:
        {skill.fields}
        
        ## Instructions:
        {skill.instructions}
        """
        
        # 3. 调用 LLM
        response = llm.chat(
            system=system_prompt,
            user=user_input
        )
        
        # 4. 可选：执行脚本
        if needs_script(response):
            result = run_script(skill.script_path)
        
        return response
```

**特点**：
- 📝 LLM 根据技能描述理解任务
- 🔄 灵活但可能不够精确
- 🎯 适合开放式任务

#### 项目 Skills 执行流程
```python
# 实际代码示例（backend/api/collection_routes.py）
ingest_skill = IngestSkill(storage)
ingest_result = await ingest_skill.execute(upload_file, project_id)

parse_skill = ParseSkill(llm_gateway)
parse_result = await parse_skill.execute(ingest_result, use_llm=True)

mapping_skill = MappingSkill()
mapping_result = mapping_skill.execute(
    project_id=project_id,
    node_id=node_id,
    structured_data=parse_result["structured_data"],
    ...
)
```

**特点**：
- ⚡ 直接执行代码，性能高
- 🎯 逻辑精确，行为可预测
- 🔒 类型安全（通过类型注解）
- 🧪 易于测试和调试

---

### 3. **元数据管理**

#### Claude Skills
```yaml
# SKILL.md 的 YAML frontmatter
---
name: pdf_parser
description: 解析PDF文件
version: 1.0.0
author: ...
tags: [pdf, parsing, table]
fields:
  input:
    - name: file_path
      type: string
      description: PDF文件路径
  output:
    - name: tables
      type: array
      description: 提取的表格数据
---
```

- 📄 元数据存储在文件中
- 🔍 可搜索和索引
- 📚 易于文档化

#### 项目现有 Skills
```python
class ParseSkill:
    """
    Vision-first parse: convert to page images and optional LLM call.
    
    Input:
        ingest_result: Dict[str, str] - 包含 object_key 和 source_hash
        use_llm: bool - 是否使用 LLM
        prompt: Optional[str] - 可选的 prompt
    
    Output:
        Dict[str, object] - 包含 parse_id, page_images, structured_data 等
    """
```

- 📝 元数据在 docstring 中
- 🔧 IDE 可以提示
- ⚠️ 不易于程序化访问

---

### 4. **字段定义**

#### Claude Skills
```yaml
# fields.yaml
input_fields:
  - name: file_path
    type: string
    required: true
    description: PDF文件路径
    
output_fields:
  - name: tables
    type: array
    description: 提取的表格数据
    items:
      type: object
```

#### 项目现有 Skills
```python
# 通过类型注解定义
from typing import Dict, List, Optional

async def execute(
    self,
    ingest_result: Dict[str, str],  # 输入类型
    use_llm: bool = False,
    prompt: Optional[str] = None,
) -> Dict[str, object]:  # 输出类型
    ...
```

**项目优势**：
- ✅ 类型检查（mypy/pyright）
- ✅ IDE 自动补全
- ✅ 运行时类型验证（Pydantic）

---

### 5. **技能注册和发现**

#### Claude Skills
```python
# 需要 Skill Registry
class SkillRegistry:
    def discover_skills(self, skills_dir):
        """扫描 skills 目录，加载所有 SKILL.md"""
        skills = []
        for skill_dir in Path(skills_dir).iterdir():
            if (skill_dir / "SKILL.md").exists():
                skill = self.loader.load_skill(skill_dir)
                skills.append(skill)
        return skills
```

#### 项目现有 Skills
```python
# 直接导入使用
from services.skills.parse_skill import ParseSkill
from services.skills.mapping_skill import MappingSkill
from services.skills.validation_skill import ValidationSkill

# 或通过 __init__.py 统一导出（当前未实现）
```

**项目现状**：
- ⚠️ 没有统一的注册机制
- ⚠️ 技能发现依赖代码导入
- 💡 **建议**：可以添加 `skill_registry.py` 统一管理

---

### 6. **配置和规则**

#### Claude Skills
- 配置可能在 YAML 文件中
- 通过 LLM 解释配置

#### 项目现有 Skills
```python
# 配置文件分离（如 mapping_skill.py）
def _load_mapping_config(self, node_id: str) -> Dict[str, Any]:
    mapping_dir = Path(__file__).resolve().parents[2] / "contracts" / "mapping"
    # 加载 YAML 配置文件
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 验证规则分离（如 validation_skill.py）
def __init__(self, rules_path: Optional[Path] = None):
    self.rules_path = rules_path or Path(...) / "validation_rules.yaml"
    self.rules = self._load_rules()
```

**项目优势**：
- ✅ 配置与代码分离
- ✅ 规则文件可独立管理
- ✅ 支持配置覆盖（rules_override）

---

## 🎯 核心差异总结

### Claude Skills 的特点
1. **声明式**：通过文档描述技能，LLM 理解执行
2. **灵活性高**：LLM 可以理解自然语言指令
3. **易于扩展**：添加新技能只需创建 SKILL.md 文件
4. **适合开放域**：处理未预定义的任务
5. **执行成本高**：每次都需要 LLM 调用
6. **精确度依赖 LLM**：可能产生不一致的结果

### 项目现有 Skills 的特点
1. **命令式**：通过代码直接实现逻辑
2. **精确度高**：行为完全可预测
3. **性能好**：直接执行，无 LLM 开销
4. **类型安全**：Python 类型注解 + 可选 Pydantic 验证
5. **易于测试**：单元测试、集成测试
6. **适合确定流程**：处理标准化的业务逻辑

---

## 💡 混合方案建议

### 方案 A：保持现有架构（推荐）
**适用于**：确定性的业务流程（如当前的数据提取、映射、验证流程）

**理由**：
- ✅ 当前业务流程是确定性的
- ✅ 性能要求高
- ✅ 需要精确的行为控制
- ✅ 已有良好的代码结构

**改进建议**：
1. 添加 `SkillRegistry` 统一管理技能
2. 统一技能的接口规范（基类或协议）
3. 添加技能元数据（通过 dataclass 或 Pydantic 模型）

### 方案 B：引入声明式 Skills（补充）
**适用于**：需要 LLM 动态处理的任务（如自然语言查询、灵活的数据转换）

**实现方式**：
```python
# 创建声明式技能目录
skills_declarative/
├── natural_language_query/
│   ├── SKILL.md
│   └── fields.yaml
└── flexible_data_transform/
    ├── SKILL.md
    └── fields.yaml

# 实现 SkillLoader 和 SkillExecutor
backend/services/skills_declarative/
├── loader.py
├── executor.py
└── registry.py
```

**混合使用场景**：
- **命令式 Skills**：确定性流程（ingest → parse → mapping → validation）
- **声明式 Skills**：灵活任务（自然语言查询、动态数据转换）

---

## 📋 具体改进建议

### 1. 添加技能注册表
```python
# backend/services/skills/registry.py
from typing import Dict, Type
from .ingest_skill import IngestSkill
from .parse_skill import ParseSkill
# ...

SKILL_REGISTRY: Dict[str, Type] = {
    "ingest": IngestSkill,
    "parse": ParseSkill,
    "mapping": MappingSkill,
    "validation": ValidationSkill,
    "chapter_generation": ChapterGenerationSkill,
    "template_profile": TemplateProfileSkill,
}

def get_skill(skill_name: str):
    return SKILL_REGISTRY.get(skill_name)
```

### 2. 统一技能接口
```python
# backend/services/skills/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """技能基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """执行技能"""
        pass
```

### 3. 技能元数据管理
```python
# 使用 Pydantic 模型定义元数据
from pydantic import BaseModel
from typing import List

class SkillMetadata(BaseModel):
    name: str
    description: str
    version: str
    input_fields: List[Dict[str, Any]]
    output_fields: List[Dict[str, Any]]
```

---

## 🎓 总结

**当前项目的 Skills 架构更适合现有的业务需求**，因为：

1. ✅ **确定性流程**：数据提取 → 映射 → 验证是标准化流程
2. ✅ **性能要求**：需要高效执行，不适合每次调用 LLM
3. ✅ **精确控制**：业务逻辑需要精确、可预测的行为
4. ✅ **已有良好基础**：代码结构清晰，易于维护

**Claude Skills 的架构更适合**：

1. 🎯 **开放域任务**：需要 LLM 理解自然语言指令
2. 🎯 **灵活处理**：处理未预定义的任务类型
3. 🎯 **快速原型**：快速添加新功能而无需编写代码

**建议**：
- 保持现有的命令式 Skills 架构
- 可以借鉴 Claude Skills 的**元数据管理**和**注册机制**
- 未来如需支持开放域任务，可以引入声明式 Skills 作为补充