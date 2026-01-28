---
name: material_strength_description
category: generation/inspection
version: 1.0.0
description: 生成材料强度检测情况章节，用于房屋质量安全鉴定报告
author: system
created: 2026-01-28
---

# Skill: material_strength_description

## Purpose
生成"材料强度检测情况"章节文字，用于结构安全鉴定报告中**【检查和检测情况 → 检测情况 → 材料强度】**小节。

## Scope

### 适用范围
- 砌体结构材料强度检测描述（砖、砌块、砂浆）
- 混凝土结构材料强度检测描述
- 适用于房屋质量安全鉴定报告、房屋检测报告

### 不适用范围
- 不做安全等级判定或危险性结论
- 不替代"分析说明"或"鉴定意见"章节
- 不进行结构承载力验算

## Inputs

### 数据来源
从 `professional_data` 表读取已确认的检测数据

### 关联 dataset_key
- `concrete_strength` - 混凝土强度检测数据
- `masonry_strength` - 砌体强度检测数据（砖、砌块）
- `mortar_strength` - 砂浆强度检测数据（可选）

### 输入数据结构示例
```json
{
  "project_id": "proj-xxx",
  "node_id": "node-xxx",
  "professional_data": [
    {
      "test_item": "混凝土抗压强度",
      "test_result": 28.5,
      "test_unit": "MPa",
      "design_strength_grade": "C25",
      "strength_estimated_mpa": 28.5,
      "test_date": "2024-10-15",
      "test_location_text": "1轴-A轴交叉柱",
      "confirmed_result": {
        "material_type": "混凝土",
        "test_method": "回弹法",
        "strength_grade": "C25",
        "rebound_strength": 28.5,
        "carbonation_depth_avg": 2.3
      },
      "evidence_refs": [...]
    }
  ]
}
```

## Outputs

### 输出格式
返回结构化的章节内容对象

```json
{
  "chapter_type": "material_strength",
  "chapter_title": "材料强度",
  "content": "采用回弹法对现场混凝土强度进行检测...",
  "summary": {
    "concrete_count": 5,
    "masonry_count": 3,
    "avg_strength": 28.5,
    "strength_unit": "MPa"
  },
  "evidence_refs": [...],
  "generation_metadata": {
    "skill_name": "material_strength_description",
    "skill_version": "1.0.0",
    "generated_at": "2026-01-28T10:00:00Z",
    "data_source": "professional_data",
    "record_count": 8
  }
}
```

### 输出内容特点
- 客观、陈述式的工程技术语言
- 包含检测方法、检测结果、规范依据
- 不包含评价性或结论性判断
- 数值精度符合工程规范要求

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
