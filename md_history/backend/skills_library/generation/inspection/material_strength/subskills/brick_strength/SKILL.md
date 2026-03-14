---
name: brick_strength
category: generation/inspection/material_strength
version: 1.0.0
description: 砌体砖强度检测描述生成（子skill）
parent_skill: material_strength_description
author: system
created: 2026-01-28
---

# Skill: brick_strength (Sub-Skill)

## Purpose
生成砌体砖强度检测情况的描述文字。

## Data Source
- `dataset_key`: `brick_strength`
- Query condition: `test_item LIKE '%砌体砖%' OR LIKE '%砖强度%'`

## Outputs
```json
{
  "has_data": true,
  "material_type": "brick",
  "title": "砌体砖强度",
  "content": "砌体砖采用回弹法检测，检测3个部位，强度等级推定为MU10，强度推定值为8.5MPa。相关检测及结果判定依据GB/T 50315-2011、GB 50003-2011执行。",
  "test_count": 3,
  "test_method": "回弹法",
  "avg_strength": 8.5,
  "strength_grade": "MU10",
  "evidence_refs": [...],
  "generation_metadata": {...}
}
```

## Dependencies
- GB/T 50315-2011《砌体工程现场检测技术标准》
- GB 50003-2011《砌体结构设计规范》

## Status
- ⚠️ **待完善** - fields.yaml, render.md, impl/parse.py需要根据concrete_strength模板创建
