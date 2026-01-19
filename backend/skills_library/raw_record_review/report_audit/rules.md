# Audit Rules Definition

此文件定义了 Report Audit Skill 所执行的具体规则逻辑。

## Rule Group 1: Consistency (一致性校验)

### R1-house_name (房屋名称一致性)
*   **Applies to**: "项目名称", "工程名称", "鉴定结论中的主语"
*   **Extraction**: `(?:项目名称|工程名称|房屋名称)[:：]\s*([^\n\r]+)`
*   **Validation**:
    *   Collecting: Collect all distinct values found in the document.
    *   Condition: `count(distinct_values) == 1`
*   **Fix Suggestion**: "统一为出现频率最高或用户指定的名称"
*   **Severity**: Major

### R1-floors (楼层数一致性)
*   **Applies to**: "地上X层", "地下Y层", "共Z层"
*   **Extraction**: `(?:地上|地下|共)\s*(\d+)\s*层`
*   **Validation**: `count(distinct_values_per_type) == 1`
*   **Fix Suggestion**: "统一楼层描述"
*   **Severity**: Major

### R1-area (建筑面积一致性)
*   **Applies to**: "XX m²", "XX 平方米"
*   **Extraction**: `(\d+(?:\.\d+)?)\s*(?:m2|㎡|平方米)`
*   **Validation**: `count(distinct_values) == 1` (Note: Consider floating point tolerance)
*   **Fix Suggestion**: "统一面积数值（通常保留2位小数）"
*   **Severity**: Major

### R1-build_year (建成年代一致性)
*   **Applies to**: "建于XXX年", "XXX年建成"
*   **Extraction**: `(\d{4})\s*年`
*   **Validation**: `count(distinct_values) == 1`
*   **Fix Suggestion**: "统一年代描述"
*   **Severity**: Major

---

## Rule Group 2: Formatting & Rounding (格式规范)

### R2-mortar-strength (砂浆抗压强度)
*   **Applies to**: "砂浆...换算值", "砂浆...推定值"
*   **Extraction**: `(?:砂浆|砌筑砂浆)抗压强度(?:换算|推定)值.*?(\d+(?:\.\d+)?)`
*   **Validation**:
    *   Format: Exactly 1 decimal place (`x.y`)
*   **Fix Suggestion**: "保留1位小数 (e.g. 5 -> 5.0)"
*   **Severity**: Minor

### R2-brick-strength (砖抗压强度)
*   **Applies to**: "砖...推定值"
*   **Extraction**: `(?:烧结|普通)砖抗压强度(?:推定)值.*?(\d+(?:\.\d+)?)`
*   **Validation**:
    *   Format: Exactly 1 decimal place
*   **Fix Suggestion**: "保留1位小数"
*   **Severity**: Minor

### R2-concrete-strength (混凝土抗压强度)
*   **Applies to**: "混凝土...推定值"
*   **Extraction**: `(?:混凝土|砼)抗压强度(?:推定)值.*?(\d+(?:\.\d+)?)`
*   **Validation**:
    *   Format: Exactly 1 decimal place
*   **Fix Suggestion**: "保留1位小数"
*   **Severity**: Minor

### R2-carbonation-depth (碳化深度)
*   **Applies to**: "碳化深度...平均值"
*   **Extraction**: `(?:碳化深度)(?:平均|实测)值.*?(\d+(?:\.\d+)?)`
*   **Validation**:
    *   **Rule A (Step)**: Value must be multiple of 0.5 (`value % 0.5 == 0`)
    *   **Rule B (Format)**: Display exactly 1 decimal place
*   **Fix Suggestion**: "修约至0.5倍数，并保留1位小数"
*   **Severity**: Major
