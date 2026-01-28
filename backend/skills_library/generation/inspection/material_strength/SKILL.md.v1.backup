---
name: material_strength_description
category: generation/inspection
version: 2.0.0
description: 材料强度检测章节编排器（父skill），负责调用子skills并组装成完整章节
author: system
created: 2026-01-28
updated: 2026-01-28
architecture: parent-child
---

# Skill: material_strength_description (Parent Skill)

## Purpose
作为**父skill**，负责编排和组装材料强度检测章节。通过调用子skills获取各类材料的检测描述，并组织成完整的章节内容。

**核心职责：**
- 决定需要输出哪些材料类型（根据数据可用性）
- 调用对应的子skills获取各材料描述
- 组装多个子段落，形成完整章节
- 合并证据引用和元数据

**不负责：**
- 直接从数据库取数（由子skills负责）
- 材料强度计算或换算（由子skills负责）
- 具体材料的描述生成（由子skills负责）

## Architecture

### 父子结构
```
material_strength (父skill)
├── concrete_strength (子skill) - 混凝土强度
├── brick_strength (子skill)    - 砌体砖强度
└── mortar_strength (子skill)   - 砂浆强度
```

### 子skills职责边界
每个子skill独立负责：
- 独立的数据源（dataset_key）
- 独立的字段契约（fields.yaml）
- 独立的描述范式（render.md）
- 独立的校验规则（validate.py）

## Scope

### 适用范围
- 房屋质量安全鉴定报告
- 建筑结构检测报告
- "检查和检测情况"章节中的"材料强度"小节

### 不适用范围
- 不做安全等级判定或危险性结论
- 不替代"分析说明"或"鉴定意见"章节
- 不进行结构承载力验算

## Inputs

### 控制参数
```json
{
  "project_id": "proj-xxx",
  "node_id": "node-xxx",
  "context": {
    "report_type": "safety_appraisal",
    "chapter_number": "5.2.1",
    "include_overview": true,
    "material_order": ["concrete", "brick", "mortar"]
  }
}
```

```

### 子skills调用策略
父skill会自动检测以下子skills的数据可用性：
1. **concrete_strength** - 如果有 `dataset_key=concrete_strength` 的数据
2. **brick_strength** - 如果有 `dataset_key=brick_strength` 的数据
3. **mortar_strength** - 如果有 `dataset_key=mortar_strength` 的数据

## Outputs

### 输出格式
```json
{
  "chapter_type": "material_strength",
  "chapter_title": "材料强度",
  "has_data": true,
  "sections": [
    {
      "material_type": "concrete",
      "title": "混凝土强度",
      "content": "采用回弹法对现场混凝土强度进行检测...",
      "skill_used": "concrete_strength",
      "evidence_refs": [...]
    },
    {
      "material_type": "brick",
      "title": "砌体砖强度",
      "content": "砌体砖采用回弹法检测...",
      "skill_used": "brick_strength",
      "evidence_refs": [...]
    }
  ],
  "assembled_content": "采用回弹法对现场混凝土强度进行检测...\n\n砌体砖采用回弹法检测...",
  "summary": {
    "material_types": ["concrete", "brick"],
    "total_test_count": 8
  },
  "evidence_refs": [...],
  "generation_metadata": {
    "skill_name": "material_strength_description",
    "skill_version": "2.0.0",
    "subskills_called": ["concrete_strength", "brick_strength"],
    "generated_at": "2026-01-28T10:00:00Z"
  }
}
```

## Orchestration Logic

### 执行流程
1. **检测数据可用性** - 查询哪些子skills有有效数据
2. **调用子skills** - 按顺序调用有数据的子skills
3. **组装段落** - 将子skills输出组装成完整章节
4. **合并证据** - 合并所有子skills的证据引用
5. **生成总述**（可选） - 如果配置了 `include_overview=true`

### 编排规则
```python
# 伪代码
available_materials = detect_available_materials(project_id, node_id)

sections = []
for material in material_order:
    if material in available_materials:
        result = call_subskill(f"{material}_strength", project_id, node_id)
        sections.append(result)

if include_overview:
    overview = generate_overview(sections)
    final_content = overview + "\n\n" + "\n\n".join([s.content for s in sections])
else:
    final_content = "\n\n".join([s.content for s in sections])
```

## Constraints

### 数据完整性约束
- 不得猜测或推断缺失的数据
- 缺失关键字段时，输出说明性文字，不抛异常
- 若无有效检测数据，输出"未进行××材料强度检测"

### 内容规范约束
- 不得使用"安全"、"危险"、"不符合要求"等结论性措辞
- 数值保留位数必须符合 `fields.yaml` 定义
- 必须注明检测方法和依据规范

### 引用约束
- 必须正确引用 evidence_refs，确保可追溯
- 生成的内容必须能被 analysis/conclusion 类 skills 引用

## Failure Strategy

### 数据缺失处理
- 若 `professional_data` 为空：
  - 输出"本次检测未对材料强度进行检测"
  - 返回 success=true，不中断报告生成流程

### 数据异常处理
- 若数据格式异常但可部分解析：
  - 生成可用部分的描述
  - 在 generation_metadata 中记录警告信息

### 错误处理
- 系统级错误（数据库连接失败等）：
  - 抛出异常，由上层 orchestrator 处理
  - 记录详细错误日志

## Dependencies

### 数据依赖
- 依赖 `info_collection` 类 skills 完成数据采集
- 依赖 `professional_data` 表的 `confirmed_result` 字段

### 规范依赖
- JGJ/T 23-2011《回弹法检测混凝土抗压强度技术规程》
- GB 50010-2010《混凝土结构设计规范》
- GB/T 50315-2011《砌体工程现场检测技术标准》

## Usage Example

### 调用方式
```python
from services.declarative_skills.executor import DeclarativeSkillExecutor

executor = DeclarativeSkillExecutor()
result = await executor.execute(
    skill_name="material_strength_description",
    project_id="proj-xxx",
    node_id="node-xxx",
    context={
        "report_type": "safety_appraisal",
        "chapter_number": "5.2.1"
    }
)
```

### 预期输出
```
采用回弹法对现场混凝土强度进行检测，共检测5个构件，检测结果表明，
其强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25，
检测结果符合设计要求。砌体砖采用回弹法检测，检测3个部位，强度等级
推定为MU10。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。
```

## Version History

- v1.0.0 (2026-01-28) - 初始版本，支持混凝土和砌体强度描述
