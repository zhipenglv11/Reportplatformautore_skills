---
name: delegate-info-recognition
display_name: "委托信息识别"
description: "从委托单、检测记录或鉴定报告中提取关键信息，包括委托单位、检测事项、房屋概况等，支持PDF/图片格式。"
version: "1.0.0"
---

# 委托信息识别 (Delegate Info Recognition)

## When to Use
当需要从以下文档中提取关键信息时使用：
- 委托单/委托书
- 房屋危险性鉴定报告
- 建筑检测报告
- 原始检测记录

## 提取字段

### 元数据 (meta)
- **control_id** - 控制编号（如：KJQR-056-2047）
- **record_no** - 原始记录编号（格式：No:xxxxx）
- **client_org** - 委托单位
- **inspection_reason** - 检测原因/委托鉴定事项
- **inspection_basis** - 检测依据/标准
- **instrument_id** - 仪器编号
- **inspection_date** - 检测日期（YYYY-MM-DD）
- **house_name** - 房屋名称

### 房屋详情 (house_details)
提取"房屋概况"部分的完整描述，包括：
- 房屋位置/地址
- 建成年份及使用现状
- 建筑面积
- 结构类型（砌体结构、框架结构等）
- 楼层数
- 主要构件及材料
- 其他重要房屋信息

## Execution Flow
1. 接收 PDF 或图片文件
2. 使用 VL 模型识别文档内容
3. 根据字段定义提取信息
4. 输出结构化 JSON 数据

## Output Formats
- JSON: 结构化数据（默认）
- CSV: 表格数据
- Excel: Excel文件

## Field Schema Source
详见 `fields.yaml` 查看完整字段定义

## How to Run
```bash
# 单文件处理
python parse.py document.pdf

# 批量处理
python parse.py file1.pdf file2.jpg -o output/ -f json

# 生成多种格式
python parse.py input.pdf -f all
```
