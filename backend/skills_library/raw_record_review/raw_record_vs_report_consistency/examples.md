# Examples: raw-record-vs-report-consistency

## Example 1: Perfect Match (PASS)

**Scenario**: Raw record date matches report date exactly, Instrument ID matches.

**JSON Output**:
```json
{
  "overall_status": "pass",
  "project_match_summary": {
    "date_check": "pass",
    "instrument_id_check": "pass",
    "record_id_check": "pass"
  },
  "checks": [
    {
      "rule_id": "R1-date",
      "item": "inspection_date",
      "status": "pass",
      "raw_record": { "value": "2023-06-18", "location": { "page": 1, "region": "Header" } },
      "report": { "value": "2023-06-18", "location": { "page": 2, "section": "Summary" } },
      "reason": "Date matches exactly.",
      "severity": "minor"
    },
    {
      "rule_id": "R2-instrument-id",
      "item": "instrument_id",
      "status": "pass",
      "raw_record": { "value": "HT-12", "location": { "page": 1, "region": "Equipment" } },
      "report": { "value": "HT-12", "location": { "page": 5, "section": "Equipment List" } },
      "reason": "Instrument ID matches.",
      "severity": "minor"
    }
  ],
  "summary": "All consistency checks passed. Raw record data aligns perfectly with the report."
}
```

---

## Example 2: Range Match (CONDITIONAL PASS)

**Scenario**: Raw record date (2023-06-18) falls within Report Appraisal Period (2023-06-15 ~ 2023-06-20).

**JSON Output**:
```json
{
  "overall_status": "pass",
  "project_match_summary": {
    "date_check": "conditional_pass",
    "instrument_id_check": "pass",
    "record_id_check": "pass"
  },
  "checks": [
    {
      "rule_id": "R1-date",
      "item": "inspection_date",
      "status": "conditional_pass",
      "raw_record": { "value": "2023-06-18", "location": { "page": 2, "region": "Date Field" } },
      "report": { "value": "2023-06-15 ~ 2023-06-20", "location": { "page": 4, "section": "General Info" } },
      "reason": "Raw record date is within the report's appraisal period.",
      "severity": "minor"
    }
  ],
  "summary": "Dates are consistent within the appraisal period."
}
```

---

## Example 3: Mismatch Found (FAIL)

**Scenario**: Instrument ID in Raw Record (HT-12) does not match Report (HT-15).

**JSON Output**:
```json
{
  "overall_status": "fail",
  "project_match_summary": {
    "date_check": "pass",
    "instrument_id_check": "fail",
    "record_id_check": "pass"
  },
  "checks": [
    {
      "rule_id": "R2-instrument-id",
      "item": "instrument_id",
      "status": "fail",
      "raw_record": {
        "value": "HT-12",
        "location": {"page": 1, "region": "Instrument No."}
      },
      "report": {
        "value": "HT-15",
        "location": {"section": "Device Info", "page": 6}
      },
      "reason": "Instrument ID mismatch detected.",
      "fix_suggestion": "Verify if the report references the wrong device or if the raw record belongs to a different setup.",
      "severity": "major"
    }
  ],
  "summary": "Date check passed, but Instrument ID mismatch detected (HT-12 vs HT-15). Artificial review required."
}
```
