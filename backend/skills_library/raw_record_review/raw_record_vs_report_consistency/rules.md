# Validation Rules: raw-record-vs-report-consistency

This document defines the logic for cross-checking consistency between Raw Records and Inspection Reports.

---

## R1: Inspection Date Consistency (Date Check)

### Definition
Verifies that the date recorded in the raw data aligns with the inspection or appraisal date stated in the report.

### Logic
Let `raw_date` be the date from the raw record.
Let `report_date` be the date (or range) from the report.

1.  **Exact Match**:
    *   If `raw_date == report_date`: Status = `pass`
2.  **Range Match (Conditional)**:
    *   If report defines a range `[start_date, end_date]`:
    *   AND `start_date <= raw_date <= end_date`: Status = `conditional_pass`
3.  **Mismatch**:
    *   If `raw_date` is outside the range or does not match the single date: Status = `fail`
4.  **Unclear**:
    *   If dates are missing, ambiguous, or unparseable text (e.g., "Mid-June"): Status = `needs_review`

### Severity
*   `conditional_pass`: **Minor** (Acceptable for appraisal periods)
*   `fail`: **Major**

---

## R2: Instrument ID Consistency (Instrument ID Check)

### Definition
Verifies that the equipment/instrument ID used in the raw record matches the equipment listed in the report.

### Logic
1.  **Normalization**:
    *   Strip whitespace.
    *   Convert to uppercase.
    *   (Optional) Handle separators like dashes if needed (e.g., treat `HT-12` and `HT12` as equivalent).
2.  **Match**:
    *   If `normalized(raw_instrument_id) == normalized(report_instrument_id)`: Status = `pass`
3.  **Mismatch**:
    *   If IDs differ after normalization: Status = `fail`
4.  **Missing Info**:
    *   If instrument ID is missing in either document: Status = `needs_review`

### Severity
*   `fail`: **Major** (Invalidates the link between data and report)

---

## R3: Raw Record ID Consistency (Record ID Check)

### Definition
Verifies that the unique identifier of the raw record is correctly cited or referenced in the report.

### Logic
1.  **Extraction**:
    *   `raw_id`: Unique ID found in header/footer of raw record.
    *   `report_cited_id`: ID referenced in "Basis of Inspection", "Appendix", or specific observation sections of the report.
2.  **Match**:
    *   If `raw_id == report_cited_id`: Status = `pass`
3.  **Mismatch**:
    *   If the report cites a different ID for this specific data point: Status = `fail`
4.  **Not Cited**:
    *   If the report does not explicitly cite a record ID: Status = `needs_review`

### Severity
*   `fail`: **Major**
