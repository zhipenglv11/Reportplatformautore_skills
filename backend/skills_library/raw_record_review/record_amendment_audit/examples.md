# 示例 (Examples)

## Case 1: 完美合规 (Pass)

**输入**:
> 表格第3行数据 `25.5` 被单横线划掉，旁边手写 `25.6`。
> 上方紧邻处有签名 `ZhangSan` 和日期 `2023.10.12`。

**输出**:
```json
{
  "overall_status": "pass",
  "summary": "所有修改均符合规范，签名日期齐全。",
  "issues": []
}
```

---

## Case 2: 涂黑且缺日期 (Fail)

**输入**:
> 实验记录页中段有一处黑块，完全盖住了下面的文字。
> 黑块旁边有一个签名 `Li`，但没有日期。

**输出**:
```json
{
  "overall_status": "fail",
  "summary": "发现严重涂改合规性问题：存在涂黑现象。",
  "issues": [
    {
      "issue_type": "overpaint",
      "severity": "major",
      "page": 1,
      "region": "Middle Left",
      "evidence_text": "[Black Block]",
      "reason_short": "内容被涂黑，原字迹不可辨认",
      "fix_suggestion": "必须保持原记录可见。如必须修改，请使用杠改。此记录可能需要主管审批或作废重写。"
    },
    {
      "issue_type": "missing_date",
      "severity": "minor",
      "page": 1,
      "region": "Middle Left",
      "evidence_text": "Signature: Li",
      "reason_short": "修改处仅有签名，缺失日期",
      "fix_suggestion": "请在签名旁补充修改日期"
    }
  ]
}
```

---

## Case 3: 签名距离过远 (Needs Review)

**输入**:
> 页脚有一个日期 `2023/11/01` 和签名。
> 正文中有一个数据修改（杠改），但旁边没有任何标记。
> 无法确定页脚的签名是否针对该修改。

**输出**:
```json
{
  "overall_status": "needs_review",
  "summary": "修改处未直接关联签名，页脚存在签名但不确定归属。",
  "issues": [
    {
      "issue_type": "signature_too_far",
      "severity": "minor",
      "page": 2,
      "region": "Row 10",
      "evidence_text": "Amended: 100 -> 101",
      "reason_short": "修改处附近无签名，页脚签名距离过远",
      "fix_suggestion": "建议在数据修改处旁补签简写姓名，以明确责任。"
    }
  ]
}
```
