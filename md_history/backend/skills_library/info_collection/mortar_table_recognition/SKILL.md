---
name: mortar-strength-recognition
display_name: 砂浆强度表格识别
description: 从砂浆强度检测报告表格（PDF/图片）中提取结构化字段，自动识别表格类型，并输出 JSON/CSV/Excel 格式。
---

# Mortar Strength Recognition Skill

## When to Use
Use this skill when users need to recognize mortar strength inspection tables and extract structured fields from them.

## Execution Flow
1. Accept a PDF or image file
2. Classify the table type (if multiple templates exist)
3. Extract structured fields according to the target schema
4. Output JSON, CSV, or Excel

## Output Formats
- JSON: Structured JSON data
- CSV: Comma-separated values
- Excel: Excel workbook

## Field Schema Source
The field list and schema live in `references/fields.md`.
Read that file before extraction and follow the exact field names and normalization rules.
Examples of expected output formats are in `examples/`.

## How to Run
From the skill root:
- `python scripts/run.py batch_process.py <pdf_or_image_paths>`

## Template Notes
- Current skill covers one known template; more templates may be added later.
- In the current template, header keywords are fixed.
- If a future template is unclear, ask for clarification and provide a short guess with rationale.

## Notes
- Keep missing fields as `null` and record any ambiguities in a short `notes` field.
