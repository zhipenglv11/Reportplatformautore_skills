# 系统架构和链路图

## 📋 概述

本文档详细说明系统的完整架构、Agent 使用的模型、以及数据流转链路。

---

## 🤖 Agent 使用的模型

### 当前配置

**位置**：`backend/config.py`

```python
llm_provider: str = "qwen"  # 默认使用 Qwen
llm_model: str = "qwen3-omni-flash-2025-12-01"  # 默认模型
```

**支持的 Provider**：
- `qwen` - 阿里云通义千问（默认）
- `openai` - OpenAI
- `siliconflow` - 硅基流动
- `moonshot` - Moonshot AI

### Agent 使用场景

#### 1. 文件类型识别（SkillOrchestrator）

**位置**：`backend/services/skill_orchestrator.py`

**使用的模型**：
- Provider: `settings.llm_provider` (默认: `qwen`)
- Model: `settings.llm_model` (默认: `qwen3-omni-flash-2025-12-01`)
- Temperature: `0.3` (降低温度以获得更确定的结果)
- Response Format: `json_object` (强制 JSON 输出)

**调用代码**：
```python
response = await self.llm_gateway.chat_completion(
    provider=settings.llm_provider,  # "qwen"
    model=settings.llm_model,        # "qwen3-omni-flash-2025-12-01"
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    temperature=0.3,
    response_format={"type": "json_object"},
)
```

**用途**：
- 识别上传文件的类型（concrete, mortar, brick, software_result, other）
- 确定应该使用哪个技能处理文件
- 返回识别置信度和理由

#### 2. 声明式技能执行（可选）

**位置**：`backend/services/declarative_skills/executor.py`

**使用的模型**：
- Provider: `settings.llm_provider` (默认: `qwen`)
- Model: `settings.llm_model` (默认: `qwen3-omni-flash-2025-12-01`)
- Temperature: `0.7` (默认)

**调用代码**：
```python
response = await self.llm_gateway.chat_completion(
    provider=provider or settings.llm_provider,
    model=model or settings.llm_model,
    messages=messages,
    temperature=kwargs.get("temperature", 0.7),
)
```

**用途**：
- 根据技能描述构建 system prompt
- 执行需要 LLM 理解的技能任务
- 目前 `concrete-table-recognition` 不使用 LLM，直接执行脚本

---

## 🔄 完整系统链路

### 链路1：智能编排流程（Agent-based）

```
┌─────────────────────────────────────────────────────────────┐
│                    用户操作                                 │
│  - 批量上传文件（混凝土、砂浆、砖强度、软件结果等）        │
│  - 点击"智能编排处理所有文件"                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  前端：CollectionDetailModal           │
        │  handleOrchestrate()                  │
        │  - 收集所有文件                       │
        │  - 构建 FormData                      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  POST /api/skill/orchestrate          │
        │  - files: [File1, File2, ...]        │
        │  - project_id, node_id               │
        │  - persist_result: true              │
        │  - use_llm_classification: true      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  后端：skill_orchestrator_routes.py    │
        │  orchestrate_files()                  │
        │  1. 保存所有文件到临时目录             │
        │  2. 计算文件哈希                      │
        │  3. 生成 run_id                       │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  文件类型识别（Agent）                 │
        │  SkillOrchestrator.classify_file()    │
        │                                       │
        │  对每个文件：                         │
        │  ├─→ 使用 LLM 识别（如果启用）        │
        │  │   ├─→ LLM Gateway                 │
        │  │   │   Provider: qwen              │
        │  │   │   Model: qwen3-omni-flash     │
        │  │   │   Temperature: 0.3            │
        │  │   │                                │
        │  │   ├─→ 构建识别 prompt             │
        │  │   │   - System: 文件类型识别助手   │
        │  │   │   - User: 文件名 + 内容预览   │
        │  │   │                                │
        │  │   └─→ 解析 JSON 响应              │
        │  │       - file_type                 │
        │  │       - skill_name                │
        │  │       - confidence                │
        │  │       - reasoning                 │
        │  │                                   │
        │  └─→ 或使用规则匹配（后备）           │
        │      - 基于文件名关键词               │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  按技能分组                            │
        │  skill_groups = {                     │
        │    "concrete-table-recognition": [    │
        │      (file1, classification1),        │
        │      (file2, classification2)         │
        │    ]                                  │
        │  }                                    │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  执行技能（按组）                      │
        │                                       │
        │  对于每个技能组：                      │
        │  ├─→ 获取技能执行器                   │
        │  │   skill_registry.get_skill()       │
        │  │                                    │
        │  └─→ 对每个文件：                     │
        │      ├─→ 执行技能脚本                │
        │      │   ScriptRunner.run_script()    │
        │      │   - python parse.py file.pdf   │
        │      │                                │
        │      ├─→ 提取结构化数据              │
        │      │   - 读取 processing_report.json│
        │      │   - 提取记录                   │
        │      │                                │
        │      ├─→ 规范化数据                  │
        │      │   _normalize_record()          │
        │      │                                │
        │      ├─→ 提交数据库                   │
        │      │   _build_payload()             │
        │      │   insert_professional_data()    │
        │      │                                │
        │      └─→ 记录执行日志                 │
        │          insert_run_log()              │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  返回批量结果                          │
        │  {                                   │
        │    "total_files": 3,                  │
        │    "successful": 2,                   │
        │    "failed": 1,                       │
        │    "results": [...]                   │
        │  }                                   │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  前端更新UI                            │
        │  - 显示每个文件的处理状态              │
        │  - 显示提取的数据                      │
        │  - 显示提交结果                        │
        └───────────────────────────────────────┘
```

### 链路2：手动选择技能流程

```
用户操作
  │
  ├─→ 上传文件
  ├─→ 选择技能（从下拉菜单）
  └─→ 点击"Run skill"
        │
        ├─→ handleExecuteSkill()
        │     └─→ onAnalyze(skillName, targetFileId)
        │
        ├─→ handleDataAnalysis()
        │     └─→ POST /api/skill/concrete-table-recognition
        │
        ├─→ 后端执行技能
        │     ├─→ 执行脚本
        │     ├─→ 提取数据
        │     └─→ 提交数据库
        │
        └─→ 返回结果 → 更新UI
```

---

## 🏗️ 系统架构图

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  React + TypeScript                                  │   │
│  │  - DataCollectionEditor                             │   │
│  │  - CollectionDetailModal                            │   │
│  │  - SkillSelector                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        API 层                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Routes                                      │   │
│  │  - /api/skill/orchestrate (智能编排)                │   │
│  │  - /api/skill/concrete-table-recognition (专用)     │   │
│  │  - /api/skill/execute (通用)                        │   │
│  │  - /api/skills/list (列出技能)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      编排层                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SkillOrchestrator                                  │   │
│  │  - classify_file() (LLM 识别)                        │   │
│  │  - _classify_by_rules() (规则匹配)                   │   │
│  │  - orchestrate_files() (批量编排)                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM Gateway                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LLMGateway                                          │   │
│  │  - chat_completion()                                 │   │
│  │  - vision_completion()                               │   │
│  │                                                       │   │
│  │  支持的 Provider:                                    │   │
│  │  - qwen (默认)                                       │   │
│  │  - openai                                            │   │
│  │  - siliconflow                                       │   │
│  │  - moonshot                                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      技能注册表                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SkillRegistry                                       │   │
│  │  - 命令式技能 (6个)                                  │   │
│  │  - 声明式技能 (动态加载)                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      技能执行层                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DeclarativeSkillExecutor                           │   │
│  │  - execute()                                        │   │
│  │    ├─→ SkillLoader.load_skill()                     │   │
│  │    ├─→ ScriptRunner.run_script()                    │   │
│  │    └─→ 返回结果                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据处理层                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - _normalize_record() (规范化)                      │   │
│  │  - _build_payload() (构建数据库payload)              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据库层                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  - insert_professional_data()                        │   │
│  │  - insert_run_log()                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 详细链路说明

### 链路1：智能编排（Agent-based）

#### 步骤1：用户批量上传

**前端**：`collection-detail-modal.tsx`

```typescript
// 用户上传多个文件
uploadedFiles = [
  { id: "1", name: "混凝土检测表.pdf", file: File },
  { id: "2", name: "砂浆强度表.pdf", file: File },
  { id: "3", name: "砖强度表.pdf", file: File },
]

// 点击"智能编排处理所有文件"
handleOrchestrate()
```

#### 步骤2：前端调用编排API

**API**：`POST /api/skill/orchestrate`

```typescript
const formData = new FormData();
uploadedFiles.forEach(file => {
  formData.append('files', file.file);
});
formData.append('project_id', projectId);
formData.append('node_id', nodeId);
formData.append('persist_result', 'true');
formData.append('use_llm_classification', 'true');

fetch('/api/skill/orchestrate', {
  method: 'POST',
  body: formData,
});
```

#### 步骤3：后端接收并保存文件

**后端**：`skill_orchestrator_routes.py`

```python
# 1. 保存所有文件到临时目录
for file in files:
    content = await file.read()
    source_hash = hashlib.sha256(content).hexdigest()
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    file_info_list.append({
        "path": tmp_path,
        "name": file.filename,
        "source_hash": source_hash,
    })
```

#### 步骤4：Agent 识别文件类型

**后端**：`skill_orchestrator.py`

```python
# 对每个文件进行识别
for file_info in file_info_list:
    if use_llm_classification:
        # 使用 LLM 识别
        classification = await skill_orchestrator.classify_file(
            file_path=file_info["path"],
            file_name=file_info["name"],
        )
    else:
        # 使用规则匹配
        classification = skill_orchestrator._classify_by_rules(
            file_info["name"]
        )
```

**LLM 调用详情**：
- **Provider**: `qwen` (从 `settings.llm_provider`)
- **Model**: `qwen3-omni-flash-2025-12-01` (从 `settings.llm_model`)
- **Temperature**: `0.3` (降低温度以获得更确定的结果)
- **Response Format**: `json_object` (强制 JSON 输出)
- **API Endpoint**: `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`

**识别 Prompt**：
```
System: 你是一个专业的文件类型识别助手...
User: 请识别以下文件：
文件名: 混凝土检测表.pdf
文件路径: /tmp/xxx.pdf
请返回 JSON 格式的识别结果。
```

**响应示例**：
```json
{
  "file_type": "concrete",
  "skill_name": "concrete-table-recognition",
  "confidence": 0.95,
  "reasoning": "文件名包含'混凝土'关键词，且内容匹配检测表格格式"
}
```

#### 步骤5：按技能分组

```python
skill_groups = {
    "concrete-table-recognition": [
        (file1, classification1),  # concrete
        (file2, classification2),  # mortar
        (file3, classification3),  # brick
    ]
}
```

#### 步骤6：执行技能

```python
for skill_name, file_group in skill_groups.items():
    # 获取技能执行器
    skill_type, executor = skill_registry.get_skill(skill_name)
    
    # 对每个文件执行
    for file_path, file_name, classification in file_group:
        # 执行脚本
        skill_result = await executor.execute(
            skill_name=skill_name,
            script_args=[str(file_path), "--format", "json"],
        )
        
        # 处理结果并提交数据库
        # ...
```

#### 步骤7：数据处理和提交

```python
# 1. 提取记录
extracted_records = parse_script_output(skill_result)

# 2. 规范化数据
for entry in extracted_records:
    normalized = _normalize_record(entry["data"], entry["table_type"])
    
    # 3. 构建数据库payload
    payload = _build_payload(
        record=entry["data"],
        project_id=project_id,
        node_id=node_id,
        run_id=run_id,
        ...
    )
    
    # 4. 插入数据库
    record_id = insert_professional_data(payload)
    
    # 5. 记录日志
    insert_run_log({...})
```

#### 步骤8：返回结果

```json
{
  "total_files": 3,
  "successful": 2,
  "failed": 1,
  "run_id": "...",
  "results": [
    {
      "file_name": "混凝土检测表.pdf",
      "classification": {
        "file_type": "concrete",
        "skill_name": "concrete-table-recognition",
        "confidence": 0.95,
        "reasoning": "..."
      },
      "success": true,
      "data": [...],
      "records": [...]
    },
    ...
  ]
}
```

---

## 🔍 模型使用详情

### Agent 模型配置

**配置文件**：`backend/config.py`

```python
llm_provider: str = "qwen"
llm_model: str = "qwen3-omni-flash-2025-12-01"
```

**环境变量**（`.env`）：
```env
LLM_PROVIDER=qwen
LLM_MODEL=qwen3-omni-flash-2025-12-01
QWEN_API_KEY=sk-xxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 模型调用链路

```
SkillOrchestrator.classify_file()
  │
  ├─→ LLMGateway.chat_completion()
  │     │
  │     ├─→ Provider: qwen
  │     ├─→ Model: qwen3-omni-flash-2025-12-01
  │     ├─→ Temperature: 0.3
  │     ├─→ Response Format: json_object
  │     │
  │     └─→ HTTP POST
  │           │
  │           └─→ https://dashscope.aliyuncs.com/
  │                 compatible-mode/v1/chat/completions
  │
  └─→ 解析 JSON 响应
        └─→ FileClassification
```

---

## 📝 系统组件清单

### 前端组件

1. **DataCollectionEditor**
   - 数据采集编辑器
   - 管理节点和文件

2. **CollectionDetailModal**
   - 文件详情模态框
   - 文件上传、技能选择、执行

3. **SkillSelector**
   - 技能选择器
   - 自动加载技能列表

### 后端服务

1. **SkillOrchestrator**
   - 文件类型识别（LLM/规则）
   - 技能路由
   - 批量编排

2. **SkillRegistry**
   - 统一技能注册表
   - 技能发现和访问

3. **DeclarativeSkillExecutor**
   - 执行声明式技能
   - 调用 LLM 或执行脚本

4. **SkillLoader**
   - 加载技能元数据
   - 解析 SKILL.md

5. **ScriptRunner**
   - 执行技能脚本
   - 捕获输出

6. **LLMGateway**
   - 统一 LLM 接口
   - 支持多 Provider

### API 端点

1. `POST /api/skill/orchestrate` - 智能编排（批量）
2. `POST /api/skill/concrete-table-recognition` - 专用接口
3. `POST /api/skill/execute` - 通用执行接口
4. `GET /api/skills/list` - 列出技能
5. `GET /api/skill/{name}/info` - 获取技能信息
6. `POST /api/skill/classify` - 仅识别文件类型

---

## 🎯 关键配置

### LLM 配置

**默认配置**：
- Provider: `qwen`
- Model: `qwen3-omni-flash-2025-12-01`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

**Agent 识别参数**：
- Temperature: `0.3` (降低以获得更确定的结果)
- Response Format: `json_object` (强制 JSON)

### 技能配置

**技能目录**：
```
D:/All_about_AI/projects/5_skills_create/
├── concrete-table-recognition/
│   ├── SKILL.md
│   └── parse.py
```

---

## 📊 数据流转

### 完整数据流

```
用户上传文件
  ↓
前端收集文件
  ↓
API: /api/skill/orchestrate
  ↓
后端保存临时文件
  ├─→ 计算 source_hash
  └─→ 生成 run_id
  ↓
Agent 识别（LLM）
  ├─→ LLM Gateway
  │   ├─→ Provider: qwen
  │   ├─→ Model: qwen3-omni-flash-2025-12-01
  │   └─→ API: DashScope
  │
  └─→ 返回分类结果
        ├─→ file_type
        ├─→ skill_name
        ├─→ confidence
        └─→ reasoning
  ↓
按技能分组
  ↓
执行技能脚本
  ├─→ ScriptRunner
  │   └─→ python parse.py file.pdf
  │
  └─→ 解析输出 JSON
  ↓
提取结构化数据
  ↓
数据规范化
  ├─→ _normalize_record()
  └─→ _build_payload()
  ↓
提交数据库
  ├─→ insert_professional_data()
  └─→ insert_run_log()
  ↓
返回结果
  ↓
前端更新UI
```

---

## 🔧 模型切换

### 切换 Provider

**方式1：修改配置文件**
```python
# backend/config.py
llm_provider: str = "openai"  # 改为 openai
llm_model: str = "gpt-4o"
```

**方式2：使用环境变量**
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-xxx
```

### 支持的 Provider

| Provider | Base URL | 示例模型 |
|----------|----------|---------|
| `qwen` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen3-omni-flash-2025-12-01` |
| `openai` | `https://api.openai.com/v1` | `gpt-4o`, `gpt-4-turbo` |
| `siliconflow` | `https://api.siliconflow.cn/v1` | 各种开源模型 |
| `moonshot` | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

---

## 📝 总结

### Agent 模型

- **Provider**: `qwen` (默认)
- **Model**: `qwen3-omni-flash-2025-12-01` (默认)
- **用途**: 文件类型识别
- **Temperature**: `0.3` (降低以获得更确定的结果)

### 系统链路

1. **用户操作** → 批量上传文件
2. **前端** → 调用编排API
3. **后端编排器** → Agent 识别文件类型
4. **技能路由** → 按类型分组
5. **技能执行** → 执行对应技能脚本
6. **数据处理** → 规范化并提交数据库
7. **返回结果** → 前端更新UI

### 关键特点

- ✅ 智能识别：使用 LLM 自动识别文件类型
- ✅ 自动路由：根据识别结果自动选择技能
- ✅ 批量处理：支持一次性处理多个文件
- ✅ 容错机制：LLM 失败时使用规则匹配
- ✅ 统一接口：通过 SkillRegistry 统一管理

---

**文档版本**：v1.0.0  
**最后更新**：2025-01-XX
