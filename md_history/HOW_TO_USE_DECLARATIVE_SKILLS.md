# 声明式 Skills 使用指南

## 📋 目录
1. [前置条件](#前置条件)
2. [配置设置](#配置设置)
3. [使用方式](#使用方式)
4. [实际示例](#实际示例)
5. [常见问题](#常见问题)

---

## 前置条件

### 1. 确认声明式 Skills 目录存在

声明式 Skills 应该存放在配置的目录中。默认路径是：
```
D:/All_about_AI/projects/5_skills_create
```

每个技能应该是一个独立的目录，包含：
- `SKILL.md` - 技能定义文件（必需）
- `fields.yaml` - 字段定义（可选）
- `parse.py` - 执行脚本（可选）

示例结构：
```
D:/All_about_AI/projects/5_skills_create/
├── concrete-table-recognition/
│   ├── SKILL.md
│   ├── fields.yaml
│   └── parse.py
└── notebooklm/
    ├── SKILL.md
    └── parse.py
```

### 2. 确认后端服务已启动

```bash
cd backend
python main.py
```

服务启动后，声明式 Skills 会自动加载。

---

## 配置设置

### 方式1：修改配置文件

编辑 `backend/config.py`：

```python
declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
enable_declarative_skills: bool = True
```

### 方式2：使用环境变量

创建或编辑 `backend/.env` 文件：

```env
DECLARATIVE_SKILLS_PATH=D:/All_about_AI/projects/5_skills_create
ENABLE_DECLARATIVE_SKILLS=true
```

---

## 使用方式

### 方式1：通过 API 调用（推荐）

#### 1.1 列出所有可用技能

```bash
# 使用 curl
curl http://localhost:8000/api/skills/list

# 使用 PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/skills/list" -Method Get
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

#### 1.2 获取技能详细信息

```bash
# 获取 concrete-table-recognition 的信息
curl http://localhost:8000/api/skill/concrete-table-recognition/info
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

#### 1.3 执行声明式 Skill（通用接口）

**使用 curl**：
```bash
curl -X POST http://localhost:8000/api/skill/execute \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**使用 PowerShell**：
```powershell
$body = @{
    skill_name = "concrete-table-recognition"
    user_input = "处理这个PDF文件"
    context = @{
        file_path = "/path/to/file.pdf"
    }
    use_llm = $false
    use_script = $true
    script_args = @("file.pdf", "--format", "json")
    provider = "qwen"
    model = "qwen3-omni-flash-2025-12-01"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/skill/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**参数说明**：
- `skill_name` (必需): 技能名称
- `user_input` (必需): 用户输入/指令
- `context` (可选): 上下文数据（字典）
- `use_llm` (可选, 默认 true): 是否使用 LLM
- `use_script` (可选, 默认 true): 是否执行脚本
- `script_args` (可选): 脚本参数列表
- `script_name` (可选): 脚本文件名（默认 "parse.py"）
- `provider` (可选): LLM provider（qwen, openai, siliconflow, moonshot）
- `model` (可选): LLM model 名称

#### 1.4 混凝土表格识别（专用接口）

**使用 curl**：
```bash
curl -X POST http://localhost:8000/api/skill/concrete-table-recognition \
  -F "file=@table.pdf" \
  -F "format=json" \
  -F "output_dir=./output"
```

**使用 PowerShell**：
```powershell
$form = @{
    file = Get-Item "table.pdf"
    format = "json"
    output_dir = "./output"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/skill/concrete-table-recognition" `
    -Method Post `
    -Form $form
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "文件": "table.pdf",
    "检测日期": "2024-10-10",
    "检测部位": "2#楼柱梁板楼面",
    "强度等级": "C30"
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

---

### 方式2：在 Python 代码中使用

#### 2.1 使用 SkillRegistry（推荐）

```python
from pathlib import Path
from services.skill_registry.registry import SkillRegistry, SkillType

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
        context={"file_path": "file.pdf"},
        use_llm=False,
        use_script=True,
        script_args=["file.pdf", "--format", "json"],
    )
    print(result)
```

#### 2.2 直接使用 DeclarativeSkillExecutor

```python
from pathlib import Path
from services.declarative_skills.executor import DeclarativeSkillExecutor

# 创建执行器
executor = DeclarativeSkillExecutor(
    skills_base_path=Path("D:/All_about_AI/projects/5_skills_create")
)

# 执行技能
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="处理这个PDF文件",
    context={"file_path": "file.pdf"},
    use_llm=False,
    use_script=True,
    script_args=["file.pdf", "--format", "json"],
    script_timeout=600,  # 10分钟超时
)

print(result)
```

#### 2.3 在 FastAPI 路由中使用

```python
from fastapi import APIRouter, HTTPException
from services.skill_registry.registry import SkillRegistry, SkillType

router = APIRouter()
registry = SkillRegistry()

@router.post("/my-custom-endpoint")
async def my_custom_endpoint(skill_name: str, user_input: str):
    try:
        skill_type, executor = registry.get_skill(skill_name)
        
        if skill_type == SkillType.DECLARATIVE:
            result = await executor.execute(
                skill_name=skill_name,
                user_input=user_input,
                use_llm=True,
                use_script=True,
            )
            return result
        else:
            raise HTTPException(400, "This endpoint only supports declarative skills")
    except ValueError as e:
        raise HTTPException(404, str(e))
```

---

### 方式3：在前端调用

#### 3.1 使用 fetch API

```typescript
// 列出所有技能
async function listSkills() {
  const response = await fetch('http://localhost:8000/api/skills/list');
  const data = await response.json();
  console.log('可用技能:', data);
  return data;
}

// 获取技能信息
async function getSkillInfo(skillName: string) {
  const response = await fetch(
    `http://localhost:8000/api/skill/${skillName}/info`
  );
  const data = await response.json();
  return data;
}

// 执行声明式 Skill
async function executeSkill(
  skillName: string,
  userInput: string,
  options?: {
    useLLM?: boolean;
    useScript?: boolean;
    scriptArgs?: string[];
    context?: Record<string, any>;
  }
) {
  const response = await fetch('http://localhost:8000/api/skill/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      skill_name: skillName,
      user_input: userInput,
      use_llm: options?.useLLM ?? true,
      use_script: options?.useScript ?? true,
      script_args: options?.scriptArgs ?? [],
      context: options?.context ?? {},
    }),
  });
  
  const data = await response.json();
  return data;
}

// 使用示例
async function example() {
  // 1. 列出技能
  const skills = await listSkills();
  console.log('声明式技能:', skills.declarative);
  
  // 2. 获取技能信息
  const info = await getSkillInfo('concrete-table-recognition');
  console.log('技能信息:', info);
  
  // 3. 执行技能
  const result = await executeSkill(
    'concrete-table-recognition',
    '处理这个PDF文件',
    {
      useLLM: false,
      useScript: true,
      scriptArgs: ['file.pdf', '--format', 'json'],
      context: { file_path: '/path/to/file.pdf' },
    }
  );
  console.log('执行结果:', result);
}
```

#### 3.2 上传文件并处理（混凝土表格识别）

```typescript
async function processConcreteTable(file: File, format: string = 'json') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('format', format);
  
  const response = await fetch(
    'http://localhost:8000/api/skill/concrete-table-recognition',
    {
      method: 'POST',
      body: formData,
    }
  );
  
  const data = await response.json();
  return data;
}

// 使用示例
const fileInput = document.querySelector('input[type="file"]');
fileInput?.addEventListener('change', async (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) {
    const result = await processConcreteTable(file, 'json');
    console.log('处理结果:', result);
  }
});
```

---

## 实际示例

### 示例1：只使用脚本执行（不使用 LLM）

```python
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="处理文件: table.pdf",
    use_llm=False,  # 不使用 LLM
    use_script=True,  # 只执行脚本
    script_args=["table.pdf", "--format", "json"],
)
```

### 示例2：只使用 LLM（不执行脚本）

```python
result = await executor.execute(
    skill_name="notebooklm",
    user_input="查询我的笔记本中关于混凝土强度的内容",
    use_llm=True,  # 使用 LLM
    use_script=False,  # 不执行脚本
    provider="qwen",
    model="qwen3-omni-flash-2025-12-01",
)
```

### 示例3：同时使用 LLM 和脚本

```python
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="分析这个PDF文件并提取关键数据",
    use_llm=True,  # 先使用 LLM 分析
    use_script=True,  # 然后执行脚本处理
    script_args=["file.pdf", "--format", "json"],
    provider="qwen",
    model="qwen3-omni-flash-2025-12-01",
)
```

### 示例4：自定义脚本参数和超时

```python
result = await executor.execute(
    skill_name="concrete-table-recognition",
    user_input="处理文件",
    use_script=True,
    script_args=["file.pdf", "--format", "excel", "--output-dir", "./output"],
    script_name="parse.py",  # 指定脚本文件名
    script_timeout=600,  # 10分钟超时
)
```

---

## 常见问题

### Q1: 技能未找到

**错误信息**：`Skill not found: concrete-table-recognition`

**解决方案**：
1. 检查 `declarative_skills_path` 配置是否正确
2. 确认技能目录存在且包含 `SKILL.md` 文件
3. 检查技能目录名称是否匹配
4. 重启后端服务

### Q2: 脚本执行失败

**错误信息**：`Script execution failed`

**解决方案**：
1. 检查脚本文件是否存在（`parse.py`）
2. 确认脚本有执行权限
3. 检查脚本的依赖是否已安装
4. 查看 `script_result.stderr` 获取详细错误信息
5. 确认脚本在技能目录下可以独立运行

### Q3: LLM 调用失败

**错误信息**：`LLM API call failed`

**解决方案**：
1. 检查 LLM provider 配置（`config.py` 中的 `llm_provider`）
2. 确认 API key 已设置（`qwen_api_key`, `openai_api_key` 等）
3. 检查网络连接
4. 查看 LLM Gateway 的日志

### Q4: 技能未自动加载

**问题**：重启服务后，新添加的技能没有出现在列表中

**解决方案**：
1. 确认技能目录结构正确（包含 `SKILL.md`）
2. 检查 `enable_declarative_skills` 是否为 `True`
3. 查看后端启动日志，确认是否有错误信息
4. 手动调用 `initialize_declarative_skills()` 重新加载

### Q5: 脚本执行超时

**错误信息**：脚本执行超时

**解决方案**：
1. 增加 `script_timeout` 参数（默认 300 秒）
2. 优化脚本性能
3. 检查脚本是否有死循环或阻塞操作

---

## 执行流程说明

当调用声明式 Skill 时，执行流程如下：

1. **加载技能**：从技能目录加载 `SKILL.md` 和 `fields.yaml`
2. **LLM 处理**（如果 `use_llm=True`）：
   - 构建 system prompt（包含技能描述和指令）
   - 调用 LLM API
   - 返回 LLM 响应
3. **脚本执行**（如果 `use_script=True` 且存在脚本）：
   - 在技能目录下执行脚本
   - 传递参数：`user_input`, `llm_response`, `context`
   - 解析脚本输出（尝试解析为 JSON）
4. **返回结果**：包含 LLM 响应、脚本结果和技能元数据

---

## 下一步

- 查看 [DECLARATIVE_SKILLS_USAGE.md](./DECLARATIVE_SKILLS_USAGE.md) 了解更多高级用法
- 查看 [QUICK_START_DECLARATIVE_SKILLS.md](./QUICK_START_DECLARATIVE_SKILLS.md) 快速开始
- 查看 [SKILL_ARCHITECTURE_COMPARISON.md](./SKILL_ARCHITECTURE_COMPARISON.md) 了解架构设计
