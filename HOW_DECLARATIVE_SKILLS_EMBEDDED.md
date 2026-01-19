# 声明式 Skills（类似 Claude Skills）嵌入系统详解

## 📋 概述

本项目实现了类似 **Claude Skills** 的声明式技能架构，通过文档描述技能而非代码实现，使系统能够灵活扩展和动态加载技能。

---

## 🏗️ 架构设计

### 1. 核心组件

#### 1.1 SkillLoader（技能加载器）
**位置**：`backend/services/declarative_skills/loader.py`

**功能**：
- 扫描技能目录，发现所有可用的声明式技能
- 解析 `SKILL.md` 文件的 YAML frontmatter
- 加载 `fields.yaml` 字段定义
- 检测脚本文件（如 `parse.py`）

**关键方法**：
```python
class SkillLoader:
    def load_skill(self, skill_name: str) -> SkillMetadata:
        """加载指定技能的元数据"""
        # 1. 读取 SKILL.md
        # 2. 解析 YAML frontmatter（name, description, version）
        # 3. 加载 fields.yaml（如果存在）
        # 4. 检测脚本文件
        # 5. 返回 SkillMetadata 对象
    
    def list_available_skills(self) -> list[str]:
        """列出所有可用的技能目录名"""
```

#### 1.2 DeclarativeSkillExecutor（技能执行器）
**位置**：`backend/services/declarative_skills/executor.py`

**功能**：
- 执行声明式技能
- 构建 system prompt（包含技能描述和指令）
- 调用 LLM Gateway 执行 LLM 任务
- 执行技能脚本（如 `parse.py`）

**执行流程**：
```python
async def execute(self, skill_name, user_input, ...):
    # 1. 加载技能元数据
    skill = self.loader.load_skill(skill_name)
    
    # 2. 构建 system prompt
    system_prompt = f"""
    # Skill: {skill.name}
    {skill.description}
    
    ## Instructions:
    {skill.content}
    
    ## Available Fields:
    {skill.fields}
    """
    
    # 3. 调用 LLM（可选）
    if use_llm:
        llm_response = await llm_gateway.chat_completion(
            system=system_prompt,
            user=user_input
        )
    
    # 4. 执行脚本（可选）
    if use_script and skill.script_path:
        script_result = script_runner.run_script(
            script_name="parse.py",
            args=script_args,
            input_data={
                "user_input": user_input,
                "llm_response": llm_response,
                "context": context
            }
        )
    
    return {
        "llm_response": llm_response,
        "script_result": script_result,
        "metadata": {...}
    }
```

#### 1.3 ScriptRunner（脚本执行器）
**位置**：`backend/services/declarative_skills/script_runner.py`

**功能**：
- 在技能目录下执行 Python 脚本
- 传递环境变量和输入数据
- 捕获脚本输出（stdout/stderr）
- 解析 JSON 输出

**执行方式**：
```python
def run_script(self, script_name, args, input_data, timeout=300):
    # 1. 切换到技能目录
    # 2. 设置环境变量
    # 3. 通过 stdin 传递 JSON 输入数据
    # 4. 执行脚本：python parse.py arg1 arg2 ...
    # 5. 捕获输出并解析 JSON
    # 6. 返回结果
```

#### 1.4 SkillRegistry（统一注册表）
**位置**：`backend/services/skill_registry/registry.py`

**功能**：
- 统一管理命令式和声明式技能
- 提供统一的技能发现和访问接口
- 支持技能类型判断

**架构**：
```python
class SkillRegistry:
    def __init__(self):
        # 命令式技能（Python 类）
        self._imperative_skills = {
            "ingest": IngestSkill,
            "parse": ParseSkill,
            ...
        }
        
        # 声明式技能（执行器）
        self._declarative_executor = DeclarativeSkillExecutor(...)
        self._declarative_skills = ["concrete-table-recognition", ...]
    
    def get_skill(self, skill_name):
        """获取技能，返回 (SkillType, instance)"""
        if skill_name in self._imperative_skills:
            return SkillType.IMPERATIVE, skill_class
        elif skill_name in self._declarative_skills:
            return SkillType.DECLARATIVE, executor
```

---

## 🔌 集成点

### 2.1 后端集成

#### 2.1.1 配置加载
**位置**：`backend/config.py`

```python
class Settings(BaseSettings):
    # 声明式 Skills 配置
    declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
    enable_declarative_skills: bool = True
```

#### 2.1.2 路由注册
**位置**：`backend/main.py`

```python
from api import declarative_skill_routes

app.include_router(declarative_skill_routes.router, prefix="/api")
```

#### 2.1.3 自动初始化
**位置**：`backend/api/declarative_skill_routes.py`

```python
# 全局技能注册表实例
skill_registry = SkillRegistry()

# 在模块加载时初始化
def initialize_declarative_skills():
    if settings.enable_declarative_skills:
        skills_base_path = Path(settings.declarative_skills_path)
        if skills_base_path.exists():
            skill_registry.initialize_declarative_skills(skills_base_path)

initialize_declarative_skills()  # 自动执行
```

**初始化时机**：
- 模块导入时自动执行
- 服务启动时自动扫描技能目录
- 无需手动调用

#### 2.1.4 API 端点

**列出技能**：
```python
@router.get("/skills/list")
async def list_skills():
    return skill_registry.list_skills()
```

**获取技能信息**：
```python
@router.get("/skill/{skill_name}/info")
async def get_skill_info(skill_name: str):
    info = skill_registry.get_skill_info(skill_name)
    return info
```

**执行技能（通用接口）**：
```python
@router.post("/skill/execute")
async def execute_skill(request: ExecuteDeclarativeSkillRequest):
    skill_type, executor = skill_registry.get_skill(request.skill_name)
    result = await executor.execute(...)
    return result
```

**执行技能（专用接口）**：
```python
@router.post("/skill/concrete-table-recognition")
async def concrete_table_recognition(file: UploadFile, ...):
    skill_type, executor = skill_registry.get_skill("concrete-table-recognition")
    result = await executor.execute(...)
    # 处理结果并提交到数据库
    return result
```

### 2.2 前端集成

#### 2.2.1 技能选择器组件
**位置**：`src/app/components/skill-selector.tsx`

**功能**：
- 自动加载可用技能列表
- 显示技能详细信息
- 支持技能选择回调

**集成方式**：
```typescript
// 在 collection-detail-modal.tsx 中使用
<SkillSelector
  selectedSkill={selectedSkill}
  onSkillSelect={(skillName) => setSelectedSkill(skillName)}
  showOnlyDeclarative={true}
/>
```

#### 2.2.2 技能执行
**位置**：`src/app/components/collection-detail-modal.tsx`

**执行流程**：
```typescript
const handleExecuteSkill = async () => {
  await onAnalyze(node.id, node.data, {
    skillName: selectedSkill,
    targetFileId: selectedFile.id,
  });
};
```

**位置**：`src/app/components/data-collection-editor.tsx`

**实际执行**：
```typescript
const handleDataAnalysis = async (nodeId, nodeData, options) => {
  const skillName = options?.skillName;
  
  // 调用专用API
  const formData = new FormData();
  formData.append('file', fileItem.file);
  formData.append('format', 'json');
  formData.append('project_id', projectId);
  formData.append('node_id', nodeId);
  formData.append('persist_result', 'true');
  
  const response = await fetch('/api/skill/concrete-table-recognition', {
    method: 'POST',
    body: formData,
  });
  
  // 处理结果并更新UI
};
```

---

## 📂 技能目录结构

### 3.1 技能存储位置

**配置路径**：`D:/All_about_AI/projects/5_skills_create`

**目录结构**：
```
5_skills_create/
├── concrete-table-recognition/
│   ├── SKILL.md              # 技能定义（必需）
│   ├── fields.yaml           # 字段定义（可选）
│   └── parse.py              # 执行脚本（可选）
│
└── notebooklm-skill-master/
    ├── SKILL.md
    └── parse.py
```

### 3.2 SKILL.md 格式

```markdown
---
name: concrete-table-recognition
description: "识别和提取混凝土表格数据..."
version: "1.0.0"
---

# 技能名称

## 触发条件
当用户需要处理混凝土检测表格时使用此技能

## 执行流程
1. 接收PDF或图片文件
2. 识别表格类型
3. 提取结构化数据
4. 输出JSON/CSV/Excel格式

## 输出格式
...
```

### 3.3 fields.yaml 格式（可选）

```yaml
input_fields:
  - name: file_path
    type: string
    required: true
    description: 文件路径

output_fields:
  - name: data
    type: array
    description: 提取的结构化数据
```

---

## 🔄 执行流程

### 4.1 完整执行流程

```
用户操作
  ↓
前端：选择技能 + 上传文件
  ↓
前端：调用 /api/skill/concrete-table-recognition
  ↓
后端：接收文件 + 参数
  ↓
后端：SkillRegistry.get_skill("concrete-table-recognition")
  ↓
后端：DeclarativeSkillExecutor.execute()
  ├─→ SkillLoader.load_skill()  # 加载元数据
  ├─→ 构建 system prompt
  ├─→ ScriptRunner.run_script()  # 执行 parse.py
  │   ├─→ 切换到技能目录
  │   ├─→ 执行：python parse.py file.pdf --format json
  │   └─→ 解析输出 JSON
  └─→ 返回结果
  ↓
后端：处理结果 + 提交数据库
  ├─→ _normalize_record()  # 规范化数据
  ├─→ _build_payload()     # 构建数据库payload
  ├─→ insert_professional_data()  # 插入数据库
  └─→ insert_run_log()     # 记录执行日志
  ↓
后端：返回结果给前端
  ↓
前端：更新UI显示结果
```

### 4.2 数据流

```
文件上传
  ↓
临时文件保存
  ↓
技能脚本执行（parse.py）
  ↓
提取结构化数据（JSON）
  ↓
数据规范化（_normalize_record）
  ↓
构建数据库payload（_build_payload）
  ↓
插入 professional_data 表
  ↓
记录 run_log
  ↓
返回结果给前端
```

---

## 🎯 关键特性

### 5.1 动态发现
- ✅ 自动扫描技能目录
- ✅ 无需修改代码即可添加新技能
- ✅ 服务启动时自动加载

### 5.2 统一接口
- ✅ SkillRegistry 统一管理
- ✅ 命令式和声明式技能共存
- ✅ 统一的 API 接口

### 5.3 灵活执行
- ✅ 支持 LLM 执行（通过 system prompt）
- ✅ 支持脚本执行（parse.py）
- ✅ 支持混合执行（LLM + 脚本）

### 5.4 数据库集成
- ✅ 自动规范化数据
- ✅ 自动提交到 Supabase
- ✅ 记录执行日志

---

## 📊 与 Claude Skills 的对比

| 特性 | Claude Skills | 本项目实现 |
|------|--------------|-----------|
| **定义方式** | SKILL.md + YAML | ✅ SKILL.md + fields.yaml |
| **执行机制** | LLM 解释执行 | ✅ LLM + 脚本执行 |
| **脚本支持** | 支持 | ✅ 支持（parse.py） |
| **元数据管理** | YAML frontmatter | ✅ YAML frontmatter |
| **字段定义** | fields.yaml | ✅ fields.yaml |
| **注册机制** | 自动发现 | ✅ 自动发现 |
| **统一接口** | 是 | ✅ 是（SkillRegistry） |

---

## 🔧 添加新技能的步骤

### 步骤 1：创建技能目录
```
D:/All_about_AI/projects/5_skills_create/
└── your-new-skill/
    ├── SKILL.md
    ├── fields.yaml  # 可选
    └── parse.py     # 可选
```

### 步骤 2：创建 SKILL.md
```markdown
---
name: your-new-skill
description: "技能描述"
version: "1.0.0"
---

# 你的技能名称

## 触发条件
当用户...时使用此技能

## 执行流程
1. ...
2. ...
```

### 步骤 3：创建脚本（可选）
```python
#!/usr/bin/env python3
# parse.py
import sys
import json

def main():
    # 从 stdin 读取输入
    input_data = json.loads(sys.stdin.read())
    
    # 处理逻辑
    result = process(input_data)
    
    # 输出 JSON
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

### 步骤 4：重启服务
- 服务会自动发现新技能
- 无需修改代码

---

## 📝 总结

声明式 Skills（类似 Claude Skills）通过以下方式嵌入系统：

1. **后端层面**：
   - SkillLoader：解析技能定义文件
   - DeclarativeSkillExecutor：执行技能
   - ScriptRunner：执行脚本
   - SkillRegistry：统一管理

2. **API 层面**：
   - `/api/skills/list` - 列出技能
   - `/api/skill/{name}/info` - 获取信息
   - `/api/skill/execute` - 通用执行
   - `/api/skill/concrete-table-recognition` - 专用接口

3. **前端层面**：
   - SkillSelector 组件：选择技能
   - 文件上传：上传文件
   - 技能执行：调用 API
   - 结果展示：显示提取的数据

4. **数据库层面**：
   - 自动规范化数据
   - 自动提交到 Supabase
   - 记录执行日志

这种架构使得系统能够：
- ✅ 灵活扩展新技能
- ✅ 无需修改核心代码
- ✅ 支持多种执行方式
- ✅ 统一管理和访问
