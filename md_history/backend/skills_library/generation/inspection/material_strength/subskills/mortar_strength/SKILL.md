---
name: mortar_strength
category: generation/inspection/material_strength
version: 1.0.0
description: 砂浆强度检测描述生成（子skill）
parent_skill: material_strength_description
author: system
created: 2026-01-28
---

# Skill: mortar_strength (Sub-Skill)

## Purpose
生成砂浆强度检测情况的描述文字。

## Data Source
- `dataset_key`: `mortar_strength`
- Query condition: `test_item LIKE '%砂浆%'`

## Outputs
```json
{
  "has_data": true,
  "material_type": "mortar",
  "title": "砂浆强度",
  "content": "砂浆强度采用回弹法检测，检测4个测点，强度推定值为5.2MPa。相关检测及结果判定依据JGJ/T 70-2009执行。",
  "test_count": 4,
  "test_method": "回弹法",
  "avg_strength": 5.2,
  "evidence_refs": [...],
  "generation_metadata": {...}
}
```

## Dependencies
- JGJ/T 70-2009《建筑砂浆基本性能试验方法标准》

## Status
- ⚠️ **待完善** - fields.yaml, render.md, impl/parse.py需要根据concrete_strength模板创建
