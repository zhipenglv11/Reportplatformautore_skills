---
name: report-audit
display_name: "鉴定报告审核"
description: "审核鉴定报告内容的一致性与格式规范，检查数值与结论正确性。"
---
# Report Audit Skill (报告审核)

## 1. Skill Description & Triggers

### Description
这是一个专门用于工程检测鉴定报告的“质量合规性审核”工具。它不修改报告，而是通过扫描报告文本，识别内容不一致（consistency）和数值格式不规范（format & rounding）的问题，并输出带有可追溯证据的审核清单。

### Triggers (User Intents)
当用户提及以下意图时调用此 Skill：
* "帮我审一遍报告"
* "报告审核 / 检查报告错误"
* "校对一致性"
* "检查数值保留小数是否正确"
* "核对砂浆强度换算值/推定值格式"
* "检查碳化深度是否为 0.5 的倍数"
* "验证房屋信息（层数/面积/年代）在文中是否前后一致"

## 2. Input/Output Contract

### Input
- **content**: string (必须) - 报告的全文内容 (来自 OCR, PDF 解析或 DOCX 提取)。
- **structure**: object (可选) - 报告的章节结构信息，如 `{"chapter_id": "title"}`。

### Output Schema (JSON)
```json
{
  "overall_status": "pass|fail|needs_review",
  "house_profile": {
    "name": "extracted_name",
    "floors": "extracted_floors",
    "area_m2": "extracted_area",
    "build_year": "extracted_year"
  },
  "checks": [
    {
      "check_type": "consistency|format",
      "rule_id": "R1-consistency|R2-mortar|R2-brick|R2-concrete|R2-carbonation",
      "status": "pass|fail|needs_review",
      "locations": [
        {
          "section": "2.1", 
          "page": 3, 
          "quote": "原文片段上下文..."
        }
      ],
      "expected": "描述预期值或规则",
      "found": "实际发现的值",
      "fix_suggestion": "建议修改意见",
      "severity": "major|minor"
    }
  ],
  "summary": "非结构化的自然语言总结，概括主要问题。"
}
```

## 3. Supported Rules

### A) 一致性校验 (Rule Group: R1)
目标：确保关键信息在“封面/摘要/概况/鉴定结论”等不同章节保持一致。
- **R1-ProjectInfo**: 检查 `house_name` (房屋名称), `floors` (层数), `area` (面积), `build_year` (年代) 在全文各处的描述是否统一。

### B) 数值格式规范 (Rule Group: R2)
目标：确保工程数值符合标准约定的修约和显示规则。
- **R2-Mortar (砂浆强度)**: 
    - 换算值/推定值：必须保留 1 位小数 (e.g., `5.0`).
- **R2-Brick (砖抗压强度)**:
    - 推定值：必须保留 1 位小数.
- **R2-Concrete (混凝土强度)**:
    - 推定值：必须保留 1 位小数.
- **R2-Carbonation (碳化深度)**:
    - 平均值：必须是 0.5 的倍数 (step=0.5).
    - 显示：必须保留 1 位小数 (e.g., `1.0`, `2.5`).

## 4. Execution Logic (Process)

1. **Extraction (信息抽取)**: 利用 Regex 或 NLP 从文本中提取关键实体和数值上下文。
2. **Normalization (归一化)**: 清理提取的文本（去除空格、单位统一）。
3. **Check (校验)**: 
   - 对比多处提取的信息进行交叉验证 (Cross-check)。
   - 对数值提取进行格式 (Decimal place) 和 步长 (Step) 检查。
4. **Reporting (报告)**: 生成包含定位证据 (Evidence) 的 JSON 报告。

## 5. Usage Example

```python
from audit_engine import run_audit

report_text = "..." # Load text
result = run_audit(report_text)
print(json.dumps(result, indent=2))
```
