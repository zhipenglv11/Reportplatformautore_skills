---
name: record-amendment-audit
display_name: "原始记录修订审核"
description: "检查原始记录涂改和修订是否符合要求，并输出需要处理的问题清单。"
---
# 原始记录涂改合规性核查 (Record Amendment Audit)

本 Skill 用于自动化检查原始记录（检测记录/现场记录）中的修改点是否符合合规性要求（GXP/ISO17025等）。

## 核心原则
1. **真实性**：涂改必须保持原有记录清晰可辨（必须“杠改”，严禁涂黑/刮擦）。
2. **可追溯性**：修改处必须有修改人的签名（或缩写）和修改日期。
3. **审慎原则**：对于无法确定的模糊图像，标记为 `needs_review`，不进行猜测。

## 执行流程

### 1. 准备阶段
- 确认输入文件（PDF/图片）已在当前上下文或指定路径中。
- **加载辅助文件**：
  - 读取 [rules.md](rules.md) 获取详细判定口径。
  - 读取 [output_schema.json](output_schema.json) 获取输出结构要求。

### 2. 核查步骤
请按以下步骤对文档进行分析：

1.  **全局扫描**：识别文档中所有的手写修改痕迹（涂改、插入、划掉）。
2.  **逐点判定**：对每一个修改点，依据 `rules.md` 进行以下三项检查：
    *   **合规性 (Legibility)**: 原字迹是否可见？是否为单杠/双杠划掉？是否存在涂黑/涂改液覆盖？
    *   **签名 (Signature)**: 修改痕迹周围规定距离内是否有独立签名？
    *   **日期 (Date)**: 修改痕迹周围规定距离内是否有日期标注？
3.  **证据留存**：记录每个问题的页码、区域（坐标或大概位置）和证据片段。

### 3. 输出结果
请直接生成一个符合 [output_schema.json](output_schema.json) 结构的 JSON 报告。
- 必须包含 `overall_status` (pass/fail/needs_review)。
- 必须包含 `issues` 列表，每一项都应有 `fix_suggestion`。

### 4. (可选) 校验
如果输出了 JSON 文件，可以使用 `python scripts/validate_output.py <json_file>` 进行 Schema 校验。

## 注意事项
- 这是一个 **Forked Context**，你的操作不会污染主对话。请在此上下文中完成所有必要的读取和分析。
- 遇到多页 PDF，请逐页处理，并在输出中明确页码。
