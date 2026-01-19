---
name: full-qa-audit
display_name: "原始记录全量质检"
description: "对原始记录执行全流程质检，包含要素合规性、逻辑校验与数据合理性检查。"
---
# Skill: full-qa-audit

## Description
This is a **Master Orchestrator Skill** designed to execute a complete Quality Assurance Pipeline on inspection projects. It coordinates three specialized sub-skills (`record-amendment-audit`, `raw-record-vs-report-consistency`, `report-audit`) to verify compliance, consistency, and correctness.

## Input Contract
*   **Raw Records**: One or more files (Images/PDFs) containing original inspection data.
*   **Report**: A final inspection/appraisal report document.

## Execution Workflow (Pipeline)

You must strictly follow this sequential process. Do not skip steps unless a "Stop Condition" is met.

### 🛑 Step 1: Raw Record Sanity Check (Foundation)
*   **Action**: Invoke the logic of **`record-amendment-audit`**.
*   **Focus**: Check for unassigned amendments, missing signatures, or illegible data.
*   **Decision Point**:
    *   If `overall_assessment` is **"C (Major Non-compliance)"** or worse: -> **TERMINATE PIPELINE**.
    *   Synthesize the findings into the "step_1_result" section of the output.
    *   Else: Proceed to Step 2.

### 🔗 Step 2: Consistency Cross-Check (Linkage)
*   **Action**: Invoke the logic of **`raw-record-vs-report-consistency`**.
*   **Focus**: Verify if Dates, Instrument IDs, and Record IDs match between the *valid* Raw Records (from Step 1) and the Report.
*   **Decision Point**:
    *   If `overall_status` is **"fail"** (e.g., mismatched instruments): -> **TERMINATE PIPELINE** (No need to audit a report based on wrong data).
    *   Synthesize the findings into the "step_2_result" section of the output.
    *   Else: Proceed to Step 3.

### 📝 Step 3: Report & Conclusion Audit (Final Product)
*   **Action**: Invoke the logic of **`report-audit`**.
*   **Focus**: Check the report's internal consistency, typos, standard compliance, and logic.
*   **Final Actions**:
    *   Synthesize the findings into the "step_3_result" section.
    *   Generate the final `overall_pipeline_conclusion`.

## Output Structure
Return a single consolidated JSON object. See `output_schema.json`.

## Best Practices
*   **Context Management**: When passing context to Step 2, prioritize the *dates* and *IDs* extracted in Step 1 to save effort.
*   **Fail Fast**: Do not waste resources auditing the grammar of a report if the raw data is invalid.
