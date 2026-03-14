---
name: concrete-table-recognition
display_name: "混凝土表格识别"
description: "识别并提取混凝土检测表格，自动分类表类型，输出 JSON/CSV/Excel 结构化数据。"
---
# 混凝土表格识别技能 (Concrete Table Recognition)

## 使用场景 (When to Use)
当用户需要处理混凝土检测表格（如回弹记录或强度结果表），自动识别表格类型，并从中提取结构化数据时使用此技能。

## 执行流程 (Execution Flow)
1. 接收 PDF 或图片文件
2. 自动分类表格类型
3. 提取结构化字段
4. 输出 JSON、CSV 或 Excel 数据

## 输出格式 (Output Formats)
- JSON: 结构化 JSON 数据
- CSV: 逗号分隔值文件
- Excel: Excel 工作簿

## 支持的表格类型 (Supported Table Types)
1. **混凝土回弹检测记录表 (控制编号 KJQR-056-215)**
   - 用途: 记录现场回弹强度，包含工程信息、原始回弹值等。

2. **混凝土强度检测结果表 (控制编号 KSQR-4.13-XC-10)**
   - 用途: 最终强度汇总表，包含推定值、平均值、标准差等。
