# Examples: Full QA Audit Pipeline

## Example 1: Critical Failure in Step 1 (Early Termination)

**Scenario**: The raw records are unsigned and full of unverified amendments. The pipeline stops immediately.

**User Query**: "Run a full QA audit on this project."

**Response**:
```json
{
  "pipeline_id": "QA-20260118-001",
  "overall_pipeline_conclusion": "TERMINATED_EARLY",
  "summary_statement": "Audit terminated at Step 1 due to critical non-compliance in raw records.",
  "step_1_raw_record_audit": {
    "status": "fail",
    "critical_issues": ["Multiple unauthorized amendments found on page 3", "Missing technician signature on page 5"],
    "summary": "Raw records lack validity. No cross-check needed."
  },
  "step_2_consistency_check": {
    "status": "skipped",
    "mismatches": [],
    "summary": "Skipped due to Step 1 failure."
  },
  "step_3_report_audit": {
    "status": "skipped",
    "issues_found": [],
    "summary": "Skipped."
  }
}
```

---

## Example 2: Inconsistency Found in Step 2

**Scenario**: Raw records are fine, but the Instrument ID in the record differs from the report.

**Response**:
```json
{
  "pipeline_id": "QA-20260118-002",
  "overall_pipeline_conclusion": "FAIL",
  "summary_statement": "Raw records are valid, but critical consistency mismatches were found between records and the report.",
  "step_1_raw_record_audit": {
    "status": "pass",
    "critical_issues": [],
    "summary": "Raw records are compliant and signed."
  },
  "step_2_consistency_check": {
    "status": "fail",
    "mismatches": ["Instrument ID mismatch: 'HT-12' (Record) vs 'HT-99' (Report)"],
    "summary": "Data source mismatch detected."
  },
  "step_3_report_audit": {
    "status": "skipped",
    "issues_found": [],
    "summary": "Audit halted to prevent validating a report based on incorrect data linkage."
  }
}
```

---

## Example 3: Full Pass

**Scenario**: All steps pass successfully.

**Response**:
```json
{
  "pipeline_id": "QA-20260118-003",
  "overall_pipeline_conclusion": "PASS",
  "summary_statement": "Project passed all QA stages. Records are valid, data is consistent, and the report is error-free.",
  "step_1_raw_record_audit": {
    "status": "pass",
    "critical_issues": [],
    "summary": "Records valid."
  },
  "step_2_consistency_check": {
    "status": "pass",
    "mismatches": [],
    "summary": "Perfect alignment between records and report."
  },
  "step_3_report_audit": {
    "status": "pass",
    "issues_found": [],
    "summary": "Report format and logic are correct."
  }
}
```
