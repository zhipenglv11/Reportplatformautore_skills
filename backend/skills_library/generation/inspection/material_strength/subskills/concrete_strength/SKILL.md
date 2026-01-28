---
name: concrete_strength
category: generation/inspection/material_strength
version: 1.0.0
description: 混凝土强度检测描述生成（子skill）
parent_skill: material_strength_description
author: system
created: 2026-01-28
---

# Skill: concrete_strength (Sub-Skill)

## Purpose

生成混凝土强度检测情况的描述文字，作为材料强度章节的一个子段落。

**职责：**
- ✅ 从 `professional_data` 读取混凝土强度数据
- ✅ 按 `fields.yaml` 规范处理数据
- ✅ 按 `render.md` 规范生成描述文字
- ✅ 返回结构化结果给父skill

---

## Scope

### 适用范围
- 混凝土回弹法检测
- 混凝土钻芯法检测
- 混凝土超声回弹综合法检测

### 不适用范围
- 砌体砖、砌块强度（由 brick_strength 负责）
- 砂浆强度（由 mortar_strength 负责）

---

## Data Source

### Dataset Key
- `dataset_key`: `concrete_strength`
- Query condition: `test_item LIKE '%混凝土%'`

### Required Fields
从 `professional_data` 表读取：
- `strength_estimated_mpa` - 强度推定值
- `design_strength_grade` - 设计强度等级
- `carbonation_depth_avg_mm` - 碳化深度平均值
- `test_date` - 检测日期
- `test_location_text` - 检测部位
- `confirmed_result` (JSONB) - 确认后的结果

---

## Inputs

```json
{
  "project_id": "proj-xxx",
  "node_id": "node-xxx",
  "context": {
    "test_method_filter": null,  // 可选：筛选特定检测方法
    "date_range": null           // 可选：日期范围
  }
}
```

---

## Outputs

```json
{
  "has_data": true,
  "material_type": "concrete",
  "title": "混凝土强度",
  "content": "采用回弹法对现场混凝土强度进行检测，共检测5个构件。检测结果表明，混凝土强度推定值在25.8~31.2MPa之间，平均值为28.5MPa，设计强度等级为C25。碳化深度平均值为2.3mm。相关检测及结果判定依据JGJ/T 23-2011、GB 50010-2010执行。",
  "test_count": 5,
  "test_method": "回弹法",
  "avg_strength": 28.5,
  "strength_range": {"min": 25.8, "max": 31.2},
  "strength_unit": "MPa",
  "carbonation_depth": 2.3,
  "evidence_refs": [...],
  "record_ids": [...],
  "generation_metadata": {
    "skill_name": "concrete_strength",
    "skill_version": "1.0.0",
    "generated_at": "2026-01-28T10:00:00Z",
    "record_count": 5,
    "test_methods_used": ["回弹法"]
  }
}
```

---

## Processing Logic

### 数据提取优先级

1. **强度值提取**：
   - 优先级1: `confirmed_result.rebound_strength`
   - 优先级2: `strength_estimated_mpa`
   - 优先级3: `test_result`

2. **强度等级提取**：
   - 优先级1: `confirmed_result.strength_grade`
   - 优先级2: `design_strength_grade`

3. **碳化深度提取**：
   - 优先级1: `confirmed_result.carbonation_depth_avg`
   - 优先级2: `carbonation_depth_avg_mm`

### 统计计算

- **平均值**：所有检测点强度值的算术平均，保留1位小数
- **范围**：最小值~最大值，各保留1位小数
- **检测数量**：有效记录的数量

---

## Validation Rules

### 数据有效性
```yaml
strength_value:
  - range: [5.0, 100.0]  # MPa
  - precision: 1

carbonation_depth:
  - range: [0.0, 50.0]   # mm
  - precision: 1

test_count:
  - min: 1
```

### 业务逻辑校验
- 如果有 `strength_grade`，检查强度值是否在等级范围±30%内
- 检测方法应为允许值之一：`["回弹法", "钻芯法", "超声回弹综合法"]`

---

## Dependencies

### 上游Dependencies
- info_collection/concrete_table_recognition

### 技术规范
- JGJ/T 23-2011《回弹法检测混凝土抗压强度技术规程》
- GB 50010-2010《混凝土结构设计规范》
- CECS 03:2007《钻芯法检测混凝土强度技术规程》

---

## Failure Handling

### 无数据
- 返回 `has_data=false`
- 不生成 `content` 字段
- 父skill会跳过此材料类型

### 数据异常
- 记录警告但继续处理
- 在 `generation_metadata.warnings` 中记录异常信息

---

## Version History

- **v1.0.0** (2026-01-28) - 初始版本，从父skill拆分而来
