---
name: concrete-table-recognition
display_name: "混凝土表格识别"
description: "识别并提取混凝土检测表格，自动分类表类型，输出 JSON/CSV/Excel 结构化数据。"
---
# Concrete Table Recognition Skill
## When to Use
Use this skill when users need to process concrete inspection tables, identify table types, and extract structured data.

## Execution Flow
1. Accept a PDF or image file
2. Classify the table type
3. Extract structured fields
4. Output JSON, CSV, or Excel

## Output Formats
- JSON: Structured JSON data
- CSV: Comma-separated values
- Excel: Excel workbook

## Supported Table Types
1. **Concrete rebound inspection record (control code KJQR-056-215)**
   - Use cases: rebound strength inspection, construction records

2. **Concrete strength result table (control code KSQR-4.13-XC-10)**
   - Use cases: rebound method strength records
