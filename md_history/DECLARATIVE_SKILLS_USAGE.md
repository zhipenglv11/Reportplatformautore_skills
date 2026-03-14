# 声明式 Skills 使用指南

## 📋 概述

项目已成功集成声明式 Skills 支持，可以与现有的命令式 Skills 共存使用。

## 🏗️ 架构说明

### 目录结构

```
backend/
├── services/
│   ├── skills/                    # 命令式 Skills（现有）
│   │   ├── ingest_skill.py
│   │   ├── parse_skill.py
│   │   └── ...
│   │
│   ├── declarative_skills/        # 声明式 Skills 支持（新增）
│   │   ├── loader.py              # 技能加载器
│   │   ├── executor.py            # 技能执行器
│   │   ├── script_runner.py      # 脚本执行器
│   │   └── models.py              # 数据模型
│   │
│   └── skill_registry/            # 统一技能注册表（新增）
│       └── registry.py            # 注册表实现
│
└── api/
    └── declarative_skill_routes.py  # 声明式 Skills API 路由
```

## ⚙️ 配置

在 `backend/config.py` 中已添加以下配置：

```python
# 声明式 Skills 配置
declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
enable_declarative_skills: bool = True
```

可以通过环境变量或 `.env` 文件覆盖：

```env
DECLARATIVE_SKILLS_PATH=D:/All_about_AI/projects/5_skills_create
ENABLE_DECLARATIVE_SKILLS=true
```

## 🚀 API 使用

### 1. 列出所有技能

```bash
GET /api/skills/list
```

**响应示例**：
```json
{
  "imperative": [
    "ingest",
    "parse",
    "mapping",
    "validation",
    "chapter_generation",
    "template_profile"
  ],
  "declarative": [
    "concrete-table-recognition",
    "notebooklm"
  ]
}
```

### 2. 获取技能信息

```bash
GET /api/skill/{skill_name}/info
```

**示例**：
```bash
GET /api/skill/concrete-table-recognition/info
```

**响应示例**：
```json
{
  "name": "concrete-table-recognition",
  "type": "declarative",
  "description": "识别和提取混凝土表格数据...",
  "version": "1.0.0",
  "has_script": true
}
```

### 3. 执行声明式 Skill（通用接口）

```bash
POST /api/skill/execute
Content-Type: application/json

{
  "skill_name": "concrete-table-recognition",
  "user_input": "处理这个PDF文件",
  "context": {
    "file_path": "/path/to/file.pdf"
  },
  "use_llm": false,
  "use_script": true,
  "script_args": ["file.pdf", "--format", "json"],
  "provider": "qwen",
  "model": "qwen3-omni-flash-2025-12-01"
}
```

**参数说明**：
- `skill_name`: 技能名称（必需）
- `user_input`: 用户输入（必需）
- `context`: 上下文数据（可选）
- `use_llm`: 是否使用 LLM（默认 true）
- `use_script`: 是否执行脚本（默认 true）
- `script_args`: 脚本参数列表（可选）
- `script_name`: 脚本文件名（可选，默认 "parse.py"）
- `provider`: LLM provider（可选）
- `model`: LLM model（可选）

### 4. 混凝土表格识别（专用接口）

```bash
POST /api/skill/concrete-table-recognition
Content-Type: multipart/form-data

file: [PDF文件]
format: json  # 可选：json, csv, excel
output_dir: ./custom_output  # 可选
```

**示例（使用 curl）**：
```bash
curl -X POST http://localhost:8000/api/skill/concrete-table-recognition \
  -F "file=@table.pdf" \
  -F "format=json"
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "文件": "table.pdf",
    "检测日期": "2024-10-10",
    "检测部位": "2#楼柱梁板楼面",
    "强度等级": "C30",
    ...
  },
  "metadata": {
    "name": "concrete-table-recognition",
    "description": "...",
    "version": "1.0.0"
  },
  "script_result": {
    "success": true,
    "returncode": 0,
    "output": {...},
    "stdout": "...",
    "stderr": ""
  }
}
```

## 💻 代码中使用

### 1. 使用 SkillRegistry

```python
from services.skill_registry.registry import SkillRegistry, SkillType
from pathlib import Path

# 创建注册表
registry = SkillRegistry()

# 初始化声明式 Skills
skills_path = Path("D:/All_about_AI/projects/5_skills_create")
registry.initialize_declarative_skills(skills_path)

# 获取技能
skill_type, skill_instance = registry.get_skill("concrete-table-recognition")

if skill_type == SkillType.DECLARATIVE:
    # 执行声明式 Skill
    result = await skill_instance.execute(
        skill_name="concrete-table-recognition",
        user_input="处理这个PDF文件",
        use_llm=False,
        use_script=True,
        script_args=["file.pdf", "--format", "json"],
    )
```

### 2. 直接使用 DeclarativeSkillExecutor

```python
from services.declarative_skills.executor import DeclarativeSkillExecutor
from pathlib import Path

executor = DeclarativeSkillExecutor(
    skills_base_path=Path("D:/All_about_AI/projects/5_skills_create")
)

result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="处理这个PDF文件",
    use_llm=False,
    use_script=True,
    script_args=["file.pdf", "--format", "json"],
)
```

## 🔧 添加新的声明式 Skill

### 步骤 1：创建技能目录

在声明式 Skills 基础目录下创建新目录：

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
description: 技能描述
version: "1.0.0"
---

# 你的技能名称

## 触发条件
当用户...时使用此技能

## 执行流程
1. ...
2. ...

## 输出格式
...
```

### 步骤 3：创建 fields.yaml（可选）

```yaml
input_fields:
  - name: file_path
    type: string
    required: true
    description: 文件路径

output_fields:
  - name: result
    type: object
    description: 处理结果
```

### 步骤 4：创建脚本（可选）

如果技能需要执行脚本，创建 `parse.py`：

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加 scripts 目录到路径
script_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(script_dir))

from scripts.your_script import main

if __name__ == "__main__":
    main()
```

### 步骤 5：重启服务

重启 FastAPI 服务，新技能会自动被发现和注册。

## ⚠️ 注意事项

### 1. 脚本执行环境

- 脚本在技能目录下执行（`cwd=skill_dir`）
- 脚本可以使用技能目录下的所有资源
- 脚本的依赖需要在技能目录的虚拟环境中安装

### 2. 环境变量

如果脚本需要环境变量（如 API keys），可以通过 `ScriptRunner` 传递：

```python
script_result = script_runner.run_script(
    script_name="parse.py",
    args=["file.pdf"],
    env={
        "QWEN_API_KEY": "your-api-key",
        "CUSTOM_VAR": "value",
    },
)
```

### 3. 脚本输出格式

- 脚本的标准输出会被尝试解析为 JSON
- 如果解析失败，会保留原始字符串输出
- 标准错误输出会单独记录

### 4. 超时设置

默认脚本执行超时为 5 分钟（300 秒），可以通过参数调整：

```python
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="...",
    script_timeout=600,  # 10 分钟
)
```

## 🐛 故障排查

### 问题 1：技能未找到

**错误**：`Skill not found: concrete-table-recognition`

**解决方案**：
1. 检查 `declarative_skills_path` 配置是否正确
2. 确认技能目录存在且包含 `SKILL.md` 文件
3. 检查技能目录名称是否匹配

### 问题 2：脚本执行失败

**错误**：`Script execution failed`

**解决方案**：
1. 检查脚本文件是否存在
2. 确认脚本有执行权限
3. 检查脚本的依赖是否已安装
4. 查看 `script_result.stderr` 获取详细错误信息

### 问题 3：LLM 调用失败

**错误**：`LLM API call failed`

**解决方案**：
1. 检查 LLM provider 配置
2. 确认 API key 已设置
3. 检查网络连接
4. 查看 LLM Gateway 的日志

## 📚 相关文档

- [集成方案文档](./DECLARATIVE_SKILLS_INTEGRATION_PLAN.md)
- [架构对比文档](./SKILL_ARCHITECTURE_COMPARISON.md)
