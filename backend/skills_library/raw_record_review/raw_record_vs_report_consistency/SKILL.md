---
name: raw-record-vs-report-consistency
display_name: "原始记录与报告一致性比对"
description: "比对原始记录与鉴定报告的一致性，检查关键字段和数据是否匹配。"
---
# Skill: raw-record-vs-report-consistency

## Description
This skill performs a cross-consistency check between **Raw Records** (original detection/inspection data) and the final **Inspection/Appraisal Report**. It verifies critical information consistency, specifically focusing on dates, instrument IDs, and record IDs.

It provides a structured JSON output highlighting discrepancies, exact matches, and conditional matches (e.g., date ranges).

## Input Contract

### Input Files
*   **Raw Records Collection**: One or more files representing the original data (Images, PDFs, or OCR Text).
*   **Inspection/Appraisal Report**: A single document representing the final report (Word, PDF, or Text).

### Prerequisites
*   The Raw Records and the Report must belong to the **same project**.
*   The Report must contain at least:
    *   Inspection/Appraisal Date (single date or date range).
    *   Instrument/Equipment ID (often found in "Methods" or "Equipment" sections).
    *   Raw Record ID or Project ID reference.

## Output Structure
The output will be a JSON object containing:
*   `overall_status`: Summary status (`pass`, `fail`, `needs_review`).
*   `project_match_summary`: High-level status for specific checks.
*   `checks`: Detailed array of individual rule validations.
*   `summary`: A human-readable text summary of the findings.

See `output_schema.json` for the exact schema definition.

## Execution Steps

1.  **Identify and Load Documents**:
    *   Ingest `raw_records` list.
    *   Ingest `report_document`.

2.  **Extract Key Fields**:
    *   **Dates**: Extract inspection dates from raw records and inspection/appraisal dates (ranges supported) from the report.
    *   **Instrument IDs**: Extract equipment identifiers from both sources.
    *   **Record IDs**: Extract record unique identifiers from raw records and citations in the report.

3.  **Data Normalization**:
    *   Normalize dates to ISO 8601 (`YYYY-MM-DD`).
    *   Normalize IDs (remove whitespace, standardize case).

4.  **Execute Validation Rules**:
    *   Apply **R1** (Date Consistency).
    *   Apply **R2** (Instrument ID Consistency).
    *   Apply **R3** (Raw Record ID Consistency).
    *   See `rules.md` for detailed logic.

5.  **Calculate Overall Status**:
    *   Determine `overall_status` based on the severity of rule results (see Logic below).

6.  **Generate Output**:
    *   Construct the JSON response with findings, evidence locations, and severity levels.

## Status Logic

| Condition | Overall Status |
| :--- | :--- |
| All checks are `pass` | `pass` |
| Only `pass` and `conditional_pass` exist | `pass` |
| Any `fail` with severity `major` | `fail` |
| Any `needs_review` (and no `fail`) | `needs_review` |
