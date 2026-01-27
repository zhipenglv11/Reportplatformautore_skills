---
name: delegate-info-recognition
display_name: "委托信息识别"
description: "自动识别委托单文档信息，支持解析PDF/图片格式并输出为JSON/CSV/Excel。"
version: "1.0.0"
---

# 委托信息识别 (Delegate Info Recognition)

## When to Use
当需要从委托单图片或PDF文件中提取关键信息，并将其结构化为数字格式以便于进一步处理或归档时使用。

## Execution Flow
1. 接收 PDF 或图片
2. 提取委托信息
3. 输出 JSON / CSV / Excel

## Output Formats
- JSON: 结构化数据
- CSV: 表格数据
- Excel: 表格文件

## Field Schema Source
详见 `fields.yaml` 查看完整字段定义

## How to Run
- `python parse.py <pdf_or_image_paths> -o output/ -f json`
