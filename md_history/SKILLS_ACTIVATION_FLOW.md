# Skills 激活方式和流程图

## 📋 概述

本文档详细说明系统中 Skills 的激活方式、执行流程和数据流转过程。

---

## 🎯 激活方式

### 1. 声明式 Skills 激活方式

#### 方式1：通过前端 UI 激活（主要方式）

**触发路径**：
```
用户操作
  ↓
数据采集编辑器 → 双击节点 → 文件详情模态框
  ↓
上传文件 → 选择技能 → 点击"Run skill"按钮
  ↓
前端调用 API → 后端执行 → 返回结果
```

**详细步骤**：

1. **用户上传文件**
   - 在数据采集编辑器中双击节点
   - 打开文件详情模态框
   - 点击"选择文件"上传 PDF 或图片

2. **选择技能**
   - 在"Declarative Skills"区域
   - 从下拉菜单选择技能（如 `concrete-table-recognition`）
   - 技能选择器自动加载可用技能列表

3. **执行技能**
   - 点击"Run skill"按钮
   - 前端调用 `onAnalyze()` 函数
   - 传递参数：`skillName`, `targetFileId`, `projectId`, `nodeId`

4. **后端处理**
   - 接收文件上传
   - 执行技能脚本
   - 提取结构化数据
   - 自动提交到数据库

5. **结果展示**
   - 前端更新文件状态
   - 显示提取的数据（JSON 格式）
   - 显示提交结果（成功/失败）

#### 方式2：通过 API 直接调用

**通用执行接口**：
```bash
POST /api/skill/execute
Content-Type: application/json

{
  "skill_name": "concrete-table-recognition",
  "user_input": "处理这个PDF文件",
  "use_llm": false,
  "use_script": true,
  "script_args": ["file.pdf", "--format", "json"]
}
```

**专用接口（混凝土表格识别）**：
```bash
POST /api/skill/concrete-table-recognition
Content-Type: multipart/form-data

file: [PDF文件]
format: json
project_id: xxx
node_id: xxx
persist_result: true
```

---

## 🔄 完整流程图

### 流程图1：前端激活流程

```
┌─────────────────────────────────────────────────────────────┐
│                    用户操作界面                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  数据采集编辑器 (DataCollectionEditor) │
        │  - 显示节点                            │
        │  - 双击节点打开详情模态框              │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  文件详情模态框 (CollectionDetailModal) │
        │  - 文件上传区域                        │
        │  - 技能选择器 (SkillSelector)          │
        │  - 执行按钮                           │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  技能选择器 (SkillSelector)            │
        │  1. 加载技能列表                       │
        │     GET /api/skills/list               │
        │  2. 加载技能详情                       │
        │     GET /api/skill/{name}/info         │
        │  3. 显示技能选项                       │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  用户操作：                            │
        │  1. 上传文件                          │
        │  2. 选择技能                          │
        │  3. 点击"Run skill"                   │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  handleExecuteSkill()                  │
        │  - 验证技能和文件                      │
        │  - 调用 onAnalyze()                    │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  handleDataAnalysis()                  │
        │  (data-collection-editor.tsx)          │
        │  - 构建 FormData                       │
        │  - 调用 API                            │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  POST /api/skill/concrete-table-       │
        │        recognition                    │
        │  - file: File                          │
        │  - format: "json"                      │
        │  - project_id: string                  │
        │  - node_id: string                     │
        │  - persist_result: true                │
        └───────────────────────────────────────┘
                            │
                            ▼
                    [后端处理]
```

### 流程图2：后端执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  后端 API: /api/skill/concrete-table-recognition           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  1. 接收文件上传                      │
        │     - 保存到临时文件                  │
        │     - 计算文件哈希 (source_hash)       │
        │     - 生成 run_id                     │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  2. 获取技能                          │
        │     skill_registry.get_skill()        │
        │     - 检查技能类型                    │
        │     - 返回 DeclarativeSkillExecutor   │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. 执行技能                          │
        │     executor.execute()                │
        │     ├─→ SkillLoader.load_skill()      │
        │     │   - 读取 SKILL.md               │
        │     │   - 解析 YAML frontmatter       │
        │     │   - 加载 fields.yaml            │
        │     │   - 检测 parse.py               │
        │     │                                 │
        │     ├─→ ScriptRunner.run_script()     │
        │     │   - 切换到技能目录              │
        │     │   - 执行: python parse.py       │
        │     │     file.pdf --format json       │
        │     │   - 捕获 stdout/stderr          │
        │     │   - 解析 JSON 输出              │
        │     │                                 │
        │     └─→ 返回 script_result            │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  4. 处理脚本输出                      │
        │     - 读取 processing_report.json     │
        │     - 提取结构化记录                  │
        │     - 规范化数据                      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  5. 提交到数据库（如果 persist_result) │
        │     For each record:                   │
        │     ├─→ _normalize_record()           │
        │     │   - 规范化字段名                │
        │     │   - 提取关键字段                │
        │     │                                 │
        │     ├─→ _build_payload()              │
        │     │   - 构建数据库 payload          │
        │     │   - 映射字段到数据库结构        │
        │     │                                 │
        │     ├─→ insert_professional_data()     │
        │     │   - 插入 professional_data 表   │
        │     │   - 返回 record_id               │
        │     │                                 │
        │     └─→ 记录执行状态                  │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  6. 记录执行日志                       │
        │     insert_run_log()                   │
        │     - run_id                          │
        │     - project_id, node_id             │
        │     - record_ids                      │
        │     - status (SUCCESS/FAILED)         │
        │     - skill_steps                     │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  7. 返回结果                           │
        │     {                                 │
        │       "success": true,                 │
        │       "data": [...],                   │
        │       "records": [...],                │
        │       "run_id": "...",                 │
        │       "source_hash": "..."             │
        │     }                                 │
        └───────────────────────────────────────┘
                            │
                            ▼
                    [返回前端]
```

### 流程图3：数据流转

```
┌─────────────────────────────────────────────────────────────┐
│                      数据流转过程                            │
└─────────────────────────────────────────────────────────────┘

原始文件 (PDF/图片)
        │
        ▼
┌──────────────────┐
│  临时文件保存     │
│  - tmp_path      │
│  - source_hash   │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  技能脚本执行     │
│  parse.py        │
│  - 输入: 文件路径 │
│  - 输出: JSON     │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  提取的记录      │
│  [               │
│    {             │
│      "table_type": "...", │
│      "data": {...}       │
│    }             │
│  ]               │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  数据规范化      │
│  _normalize_record() │
│  - 统一字段名    │
│  - 提取关键值    │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  构建数据库Payload │
│  _build_payload()  │
│  - record_code    │
│  - test_location  │
│  - strength_*    │
│  - ...            │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  插入数据库      │
│  professional_data│
│  - 返回 record_id │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  记录执行日志     │
│  run_log         │
│  - 记录执行状态  │
│  - 记录技能步骤  │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  返回前端        │
│  - 规范化数据    │
│  - 提交结果      │
│  - 元数据        │
└──────────────────┘
```

---

## 📝 详细步骤说明

### 步骤1：前端技能加载

**组件**：`SkillSelector`

**流程**：
```typescript
useEffect(() => {
  // 1. 加载技能列表
  fetch('/api/skills/list')
    .then(res => res.json())
    .then(data => {
      setSkills(data); // {imperative: [...], declarative: [...]}
    });
  
  // 2. 加载技能详情
  data.declarative.forEach(skillName => {
    fetch(`/api/skill/${skillName}/info`)
      .then(res => res.json())
      .then(detail => {
        setSkillDetails(prev => ({
          ...prev,
          [skillName]: detail
        }));
      });
  });
}, []);
```

**触发时机**：组件挂载时自动执行

---

### 步骤2：用户选择技能

**组件**：`CollectionDetailModal`

**流程**：
```typescript
// 用户从下拉菜单选择技能
<SkillSelector
  selectedSkill={selectedSkill}
  onSkillSelect={(skillName) => {
    setSelectedSkill(skillName); // 保存选中的技能
  }}
/>
```

**状态更新**：
- `selectedSkill` 状态更新
- 技能描述显示在下方

---

### 步骤3：用户点击执行

**组件**：`CollectionDetailModal`

**流程**：
```typescript
const handleExecuteSkill = async () => {
  // 验证
  if (!selectedSkill || !selectedFile?.file) {
    alert('请选择技能和文件');
    return;
  }
  
  // 调用父组件的分析函数
  await onAnalyze(node.id, node.data, {
    skillName: selectedSkill,
    targetFileId: selectedFile.id,
  });
};
```

**参数传递**：
- `skillName`: 选中的技能名称
- `targetFileId`: 要处理的文件ID
- `node.id`: 节点ID
- `node.data`: 节点数据

---

### 步骤4：前端API调用

**组件**：`DataCollectionEditor`

**流程**：
```typescript
const handleDataAnalysis = async (nodeId, nodeData, options) => {
  const skillName = options?.skillName;
  const targetFileId = options?.targetFileId;
  
  // 获取目标文件
  const targetFiles = targetFileId
    ? files.filter(f => f.id === targetFileId)
    : files;
  
  // 为每个文件调用API
  await Promise.all(targetFiles.map(async (fileItem) => {
    const formData = new FormData();
    formData.append('file', fileItem.file);
    formData.append('format', 'json');
    formData.append('project_id', projectId);
    formData.append('node_id', nodeId);
    formData.append('persist_result', 'true');
    
    const response = await fetch(
      '/api/skill/concrete-table-recognition',
      {
        method: 'POST',
        body: formData,
      }
    );
    
    const result = await response.json();
    return { id: fileItem.id, result };
  }));
};
```

**API 端点**：`POST /api/skill/concrete-table-recognition`

**请求参数**：
- `file`: 文件对象（multipart/form-data）
- `format`: 输出格式（json/csv/excel）
- `project_id`: 项目ID
- `node_id`: 节点ID
- `persist_result`: 是否提交到数据库（true/false）

---

### 步骤5：后端接收请求

**路由**：`declarative_skill_routes.py`

**流程**：
```python
@router.post("/skill/concrete-table-recognition")
async def concrete_table_recognition(
    file: UploadFile,
    format: str = Form("json"),
    project_id: Optional[str] = Form(None),
    node_id: Optional[str] = Form(None),
    persist_result: bool = Form(True),
):
    # 1. 保存文件到临时目录
    tmp_path = save_temp_file(file)
    source_hash = calculate_hash(file)
    run_id = generate_uuid()
    
    # 2. 获取技能执行器
    skill_type, executor = skill_registry.get_skill(
        "concrete-table-recognition"
    )
    
    # 3. 执行技能
    result = await executor.execute(...)
    
    # 4. 处理结果并提交数据库
    # ...
```

---

### 步骤6：技能执行

**组件**：`DeclarativeSkillExecutor`

**流程**：
```python
async def execute(self, skill_name, user_input, ...):
    # 1. 加载技能元数据
    skill = self.loader.load_skill(skill_name)
    # 返回: SkillMetadata(name, description, script_path, ...)
    
    # 2. 执行脚本（如果 use_script=True）
    if use_script and skill.script_path:
        script_result = script_runner.run_script(
            script_name="parse.py",
            args=["file.pdf", "--format", "json"],
            timeout=300
        )
    
    return {
        "script_result": script_result,
        "metadata": {...}
    }
```

**脚本执行**：
```python
# ScriptRunner.run_script()
# 1. 切换到技能目录
# 2. 执行: python parse.py file.pdf --format json
# 3. 捕获输出
# 4. 解析 JSON
# 5. 返回结果
```

---

### 步骤7：数据处理和提交

**组件**：`declarative_skill_routes.py`

**流程**：
```python
# 1. 提取记录
extracted_records = []
for entry in script_output:
    extracted_records.append({
        "table_type": entry.get("type"),
        "data": entry.get("data")
    })

# 2. 规范化数据
for entry in extracted_records:
    normalized = _normalize_record(entry["data"], entry["table_type"])
    
    # 3. 构建数据库payload
    if persist_result:
        payload = _build_payload(
            record=entry["data"],
            project_id=project_id,
            node_id=node_id,
            run_id=run_id,
            ...
        )
        
        # 4. 插入数据库
        record_id = insert_professional_data(payload)
        
        # 5. 记录结果
        record_results.append({
            "status": "success" if record_id else "failed",
            "record_id": record_id,
            "data": normalized
        })

# 6. 记录执行日志
insert_run_log({
    "run_id": run_id,
    "status": "SUCCESS",
    "skill_steps": {...}
})
```

---

### 步骤8：返回结果

**响应格式**：
```json
{
  "success": true,
  "data": [
    {
      "控制编号": "...",
      "检测部位": "...",
      "强度等级": "...",
      ...
    }
  ],
  "records": [
    {
      "chunk_id": "skill-1",
      "status": "success",
      "record_id": "xxx",
      "data": {...}
    }
  ],
  "run_id": "...",
  "source_hash": "...",
  "metadata": {
    "name": "concrete-table-recognition",
    "version": "1.0.0"
  }
}
```

---

### 步骤9：前端更新UI

**组件**：`DataCollectionEditor`

**流程**：
```typescript
// 1. 更新文件状态
const nextFiles = files.map(file => {
  if (file.id === result.id) {
    return {
      ...file,
      status: result.success ? 'uploaded' : 'failed',
      skill_result: result.result,
      commit_results: result.result.records,
      confirmed: result.result.records.every(r => r.status === 'success')
    };
  }
  return file;
});

// 2. 更新分析结果
const analysisResult = {
  nodeId,
  nodeLabel: nodeData.label,
  analyzedAt: new Date().toLocaleString('zh-CN'),
  jsonData: structuredData
};

// 3. 更新状态
setUploadedFiles(prev => ({ ...prev, [nodeId]: nextFiles }));
setAnalysisResults(prev => ({ ...prev, [nodeId]: analysisResult }));
```

**UI 更新**：
- 文件状态显示为"已解析"
- 右侧面板显示提取的 JSON 数据
- 显示提交结果（成功/失败）

---

## 🎯 关键激活点

### 激活点1：服务启动时

**位置**：`backend/api/declarative_skill_routes.py`

```python
# 模块加载时自动执行
def initialize_declarative_skills():
    if settings.enable_declarative_skills:
        skills_base_path = Path(settings.declarative_skills_path)
        skill_registry.initialize_declarative_skills(skills_base_path)

initialize_declarative_skills()  # 自动执行
```

**作用**：
- 扫描技能目录
- 加载所有声明式技能
- 注册到 SkillRegistry

---

### 激活点2：前端组件挂载时

**位置**：`src/app/components/skill-selector.tsx`

```typescript
useEffect(() => {
  loadSkills(); // 自动加载技能列表
}, []);
```

**作用**：
- 获取可用技能列表
- 加载技能详细信息
- 更新 UI 显示

---

### 激活点3：用户点击执行按钮

**位置**：`src/app/components/collection-detail-modal.tsx`

```typescript
<button onClick={handleExecuteSkill}>
  Run skill
</button>
```

**作用**：
- 触发技能执行流程
- 调用后端 API
- 处理执行结果

---

## 📊 流程图总结

### 完整流程图（简化版）

```
用户操作
  │
  ├─→ 上传文件
  │     │
  │     └─→ 文件保存到内存
  │
  ├─→ 选择技能
  │     │
  │     ├─→ SkillSelector 加载技能列表
  │     │     └─→ GET /api/skills/list
  │     │
  │     └─→ 显示技能选项
  │
  └─→ 点击"Run skill"
        │
        ├─→ handleExecuteSkill()
        │     └─→ onAnalyze(skillName, targetFileId)
        │
        ├─→ handleDataAnalysis()
        │     └─→ POST /api/skill/concrete-table-recognition
        │
        ├─→ 后端接收请求
        │     ├─→ 保存临时文件
        │     ├─→ 获取技能执行器
        │     └─→ 执行技能
        │           ├─→ 加载 SKILL.md
        │           ├─→ 执行 parse.py
        │           └─→ 解析输出
        │
        ├─→ 数据处理
        │     ├─→ 规范化数据
        │     ├─→ 构建数据库payload
        │     ├─→ 插入数据库
        │     └─→ 记录日志
        │
        └─→ 返回结果
              │
              └─→ 前端更新UI
                    ├─→ 更新文件状态
                    ├─→ 显示提取数据
                    └─→ 显示提交结果
```

---

## 🔑 关键配置

### 后端配置

**位置**：`backend/config.py`

```python
declarative_skills_path: str = "D:/All_about_AI/projects/5_skills_create"
enable_declarative_skills: bool = True
```

### 技能目录结构

```
D:/All_about_AI/projects/5_skills_create/
├── concrete-table-recognition/
│   ├── SKILL.md          # 必需
│   ├── fields.yaml       # 可选
│   └── parse.py          # 可选
```

---

## 📝 总结

### 激活方式

1. **自动激活**：
   - 服务启动时自动扫描技能目录
   - 前端组件挂载时自动加载技能列表

2. **用户激活**：
   - 上传文件
   - 选择技能
   - 点击执行按钮

### 执行流程

1. **前端**：文件上传 → 技能选择 → API 调用
2. **后端**：接收文件 → 执行技能 → 处理数据 → 提交数据库
3. **返回**：结果数据 → 前端更新 UI

### 数据流转

文件 → 临时文件 → 脚本执行 → JSON 数据 → 规范化 → 数据库 → 返回前端

---

**文档版本**：v1.0.0  
**最后更新**：2025-01-XX
