---
name: structure-damage-alterations-recognition
display_name: 结构损伤与变动识别
description: 从结构损伤/变动检测表格（PDF/图片）中提取结构化字段，并输出 JSON/CSV/Excel 格式。
version: "1.0.0"
---

# Structure Damage and Alterations Recognition

## When to Use
Use this skill to extract structured data from structure damage/alteration inspection tables.

## Execution Flow
1. Accept a PDF or image file
2. Parse table structure and extract fields
3. Output JSON/CSV/Excel

## Field Schema Source
The field list and schema live in `references/fields.md`.
Read that file before extraction and follow the exact field names and normalization rules.

## How to Run
From the skill root:
- `python scripts/run.py batch_process.py <pdf_or_image_paths>`

## Notes
- Keep missing fields as `null`.
- If the table is ambiguous, add a short `notes` field to explain.
