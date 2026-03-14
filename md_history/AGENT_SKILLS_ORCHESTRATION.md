# Agent Skills 编排系统

## 📋 概述

实现了基于 Agent 的智能编排系统，支持：
- ✅ 批量上传多个文件
- ✅ 自动识别文件类型（使用 LLM 或规则匹配）
- ✅ 智能路由到对应的技能
- ✅ 自动执行信息提取任务
- ✅ 批量提交到数据库

---

## 🎯 核心功能

### 1. 文件类型识别

**支持的文件类型**：
- `concrete`: 混凝土强度检测表
- `mortar`: 砂浆强度检测表
- `brick`: 砖强度检测表
- `software_result`: 软件计算结果表
- `other`: 其他类型

**识别方式**：
1. **LLM 识别**（推荐）：使用 LLM 分析文件名和内容
2. **规则匹配**（后备）：基于文件名关键词匹配

### 2. 智能路由

**路由规则**：
```python
file_type_to_skill = {
    "concrete": "concrete-table-recognition",
    "mortar": "concrete-table-recognition",
    "brick": "concrete-table-recognition",
    "software_result": "concrete-table-recognition",
}
```

### 3. 批量处理

- 支持一次性上传多个文件
- 自动识别每个文件的类型
- 按技能分组执行
- 并行处理提高效率

---

## 🔄 完整流程图

```
用户操作：批量上传文件
  ↓
前端：收集所有文件
  ↓
前端：调用 POST /api/skill/orchestrate
  │   - files: [File1, File2, File3, ...]
  │   - project_id: xxx
  │   - node_id: xxx
  │   - persist_result: true
  │   - use_llm_classification: true
  ↓
后端：接收文件
  ├─→ 保存到临时文件
  ├─→ 计算文件哈希
  └─→ 生成 run_id
  ↓
后端：识别文件类型（SkillOrchestrator）
  ├─→ 对每个文件：
  │   ├─→ 使用 LLM 识别（如果 use_llm_classification=true）
  │   │   ├─→ 构建识别 prompt
  │   │   ├─→ 调用 LLM API
  │   │   └─→ 解析识别结果
  │   │
  │   └─→ 或使用规则匹配（后备方案）
  │       └─→ 基于文件名关键词匹配
  ↓
后端：按技能分组
  ├─→ concrete-table-recognition: [File1, File2]
  ├─→ other-skill: [File3]
  └─→ 无匹配: [File4] → 记录错误
  ↓
后端：执行技能（按组）
  ├─→ 对于每个技能组：
  │   ├─→ 获取技能执行器
  │   ├─→ 对每个文件：
  │   │   ├─→ 执行技能脚本
  │   │   ├─→ 提取结构化数据
  │   │   ├─→ 规范化数据
  │   │   ├─→ 提交数据库（如果 persist_result=true）
  │   │   └─→ 记录执行日志
  │   └─→ 收集结果
  ↓
后端：返回批量结果
  ├─→ 统计成功/失败数量
  ├─→ 返回每个文件的处理结果
  └─→ 包含分类信息、提取数据、提交状态
  ↓
前端：更新UI
  ├─→ 显示每个文件的处理状态
  ├─→ 显示提取的数据
  └─→ 显示提交结果
```

---

## 🚀 API 使用

### 1. 批量编排接口

**端点**：`POST /api/skill/orchestrate`

**请求格式**：
```bash
POST /api/skill/orchestrate
Content-Type: multipart/form-data

files: [File1, File2, File3, ...]  # 多个文件
project_id: xxx
node_id: xxx
persist_result: true
use_llm_classification: true  # 是否使用 LLM 识别
```

**响应格式**：
```json
{
  "total_files": 3,
  "successful": 2,
  "failed": 1,
  "run_id": "...",
  "results": [
    {
      "file_name": "concrete_table.pdf",
      "classification": {
        "file_type": "concrete",
        "skill_name": "concrete-table-recognition",
        "confidence": 0.95,
        "reasoning": "文件名包含'混凝土'关键词，且内容匹配检测表格格式"
      },
      "success": true,
      "data": [...],
      "records": [...]
    },
    {
      "file_name": "mortar_test.pdf",
      "classification": {
        "file_type": "mortar",
        "skill_name": "concrete-table-recognition",
        "confidence": 0.88,
        "reasoning": "..."
      },
      "success": true,
      "data": [...],
      "records": [...]
    },
    {
      "file_name": "unknown.pdf",
      "classification": {
        "file_type": "other",
        "skill_name": null,
        "confidence": 0.3,
        "reasoning": "无法识别文件类型"
      },
      "success": false,
      "error": "未找到匹配的技能，文件类型: other"
    }
  ]
}
```

### 2. 文件分类接口（仅识别，不执行）

**端点**：`POST /api/skill/classify`

**请求格式**：
```bash
POST /api/skill/classify
Content-Type: multipart/form-data

file: [File]
use_llm: true
```

**响应格式**：
```json
{
  "file_name": "concrete_table.pdf",
  "classification": {
    "file_type": "concrete",
    "skill_name": "concrete-table-recognition",
    "confidence": 0.95,
    "reasoning": "识别理由..."
  }
}
```

---

## 💻 前端集成

### 添加批量上传和智能编排功能

在 `collection-detail-modal.tsx` 中添加：

```typescript
// 批量上传和智能编排
const handleBatchOrchestrate = async () => {
  if (uploadedFiles.length === 0) {
    alert('请先上传文件');
    return;
  }

  setIsExecutingSkill(true);
  try {
    const formData = new FormData();
    
    // 添加所有文件
    uploadedFiles.forEach((fileItem) => {
      if (fileItem.file) {
        formData.append('files', fileItem.file);
      }
    });
    
    formData.append('project_id', projectId);
    formData.append('node_id', node.id);
    formData.append('persist_result', 'true');
    formData.append('use_llm_classification', 'true');

    const response = await fetch('/api/skill/orchestrate', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('编排执行失败');
    }

    const result = await response.json();
    
    // 处理结果
    console.log('批量处理结果:', result);
    alert(`处理完成：成功 ${result.successful} 个，失败 ${result.failed} 个`);
    
    // 更新文件状态
    // ...
  } catch (error: any) {
    console.error('编排执行失败:', error);
    alert(`执行失败: ${error.message}`);
  } finally {
    setIsExecutingSkill(false);
  }
};
```

---

## 🔧 配置和扩展

### 添加新的文件类型

在 `skill_orchestrator.py` 中：

```python
# 1. 更新文件类型到技能的映射
self.file_type_to_skill = {
    "concrete": "concrete-table-recognition",
    "mortar": "concrete-table-recognition",
    "brick": "concrete-table-recognition",
    "software_result": "concrete-table-recognition",
    "new_type": "new-skill-name",  # 添加新类型
}

# 2. 更新规则匹配
def _classify_by_rules(self, file_name: str):
    if "新类型关键词" in file_name.lower():
        return FileClassification(
            file_type="new_type",
            skill_name="new-skill-name",
            ...
        )
```

### 添加新的技能

1. 在技能目录创建新技能
2. 更新 `file_type_to_skill` 映射
3. 更新 LLM 识别 prompt（可选）

---

## 📊 优势

### 1. 用户体验
- ✅ 一次性上传所有文件，无需逐个处理
- ✅ 自动识别文件类型，无需手动选择
- ✅ 智能路由，自动选择正确的技能

### 2. 系统效率
- ✅ 批量处理，提高吞吐量
- ✅ 按技能分组，减少重复初始化
- ✅ 并行处理，提高执行速度

### 3. 可扩展性
- ✅ 易于添加新的文件类型
- ✅ 易于添加新的技能
- ✅ 支持 LLM 和规则两种识别方式

---

## 🎯 使用场景

### 场景1：混合文件类型

用户上传：
- `混凝土回弹检测表.pdf`
- `砂浆强度结果表.pdf`
- `砖强度检测表.pdf`
- `软件计算结果.xlsx`

系统自动：
1. 识别每个文件的类型
2. 路由到对应的技能（目前都使用 `concrete-table-recognition`）
3. 执行提取任务
4. 提交到数据库

### 场景2：单一类型批量

用户上传：
- `检测表1.pdf`
- `检测表2.pdf`
- `检测表3.pdf`

系统自动：
1. 识别为同一类型（concrete）
2. 使用同一技能批量处理
3. 提高处理效率

---

## 📝 实现细节

### 文件类型识别 Prompt

```python
system_prompt = """你是一个专业的文件类型识别助手。
可用的技能：
1. concrete-table-recognition: 用于识别和提取混凝土、砂浆、砖强度等检测表格数据

文件类型包括：
- concrete: 混凝土强度检测表
- mortar: 砂浆强度检测表
- brick: 砖强度检测表
- software_result: 软件计算结果表
- other: 其他类型

请根据文件名和内容识别文件类型，并返回 JSON 格式。
"""
```

### 规则匹配关键词

```python
# 混凝土
["混凝土", "concrete", "回弹", "rebound"]

# 砂浆
["砂浆", "mortar"]

# 砖
["砖", "brick"]

# 软件结果
["软件", "software", "计算", "result"]
```

---

## 🚀 快速开始

### 1. 测试文件分类

```bash
curl -X POST http://localhost:8000/api/skill/classify \
  -F "file=@test.pdf" \
  -F "use_llm=true"
```

### 2. 测试批量编排

```bash
curl -X POST http://localhost:8000/api/skill/orchestrate \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "files=@file3.pdf" \
  -F "project_id=xxx" \
  -F "node_id=xxx" \
  -F "persist_result=true" \
  -F "use_llm_classification=true"
```

---

## 📚 相关文档

- [声明式 Skills 使用指南](./HOW_TO_USE_DECLARATIVE_SKILLS.md)
- [Skills 激活流程](./SKILLS_ACTIVATION_FLOW.md)
- [声明式 Skills 嵌入详解](./HOW_DECLARATIVE_SKILLS_EMBEDDED.md)

---

**版本**：v1.0.0  
**最后更新**：2025-01-XX
