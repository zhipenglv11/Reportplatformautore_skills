---
name: inspection_content_and_methods
category: generation/inspection
version: 1.0.0
description: 生成"鉴定内容和方法及原始记录一览表"章节，包含鉴定内容、方法、仪器设备和原始记录清单
author: system
created: 2026-02-15
architecture: standalone
---

# Skill: inspection_content_and_methods

## Purpose
生成房屋危险性鉴定报告的第三章"鉴定内容和方法及原始记录一览表"，包括：
- 鉴定内容和方法
- 主要检测仪器设备
- 原始记录一览表

## Scope

### 适用范围
- 房屋危险性鉴定报告
- 房屋安全鉴定报告
- 建筑结构检测报告

### 章节位置
通常作为报告的第三章，位于"基本情况和房屋概况"之后，"检查和检测情况"之前

## Inputs

### 控制参数
```json
{
  "project_id": "proj-xxx",
  "node_id": "node-xxx",
  "context": {
    "report_type": "danger_appraisal",
    "chapter_number": "三",
    "include_foundation": true,
    "include_superstructure": true,
    "include_enclosure": true
  }
}
```

## Outputs

### 输出格式
```json
{
  "chapter_type": "inspection_content_and_methods",
  "chapter_title": "鉴定内容和方法及原始记录一览表",
  "has_data": true,
  "sections": [
    {
      "section_number": "(一)",
      "section_title": "鉴定内容和方法",
      "content": "..."
    },
    {
      "section_number": "(二)",
      "section_title": "主要检测仪器设备",
      "content": "...",
      "table": {...}
    },
    {
      "section_number": "(三)",
      "section_title": "原始记录一览表",
      "content": "...",
      "table": {...}
    }
  ],
  "generation_metadata": {
    "skill_name": "inspection_content_and_methods",
    "skill_version": "1.0.0",
    "generated_at": "2026-02-15T10:00:00Z"
  }
}
```

## Field Schema
详见 `fields.yaml`
