from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from contracts.record_registry import resolve_expected_type, resolve_record_name, resolve_record_type

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized: Dict[str, Any]
    policy: Dict[str, str]


class ValidationSkill:
    """Minimal validation rules for concrete strength results."""

    def __init__(self, rules_path: Optional[Path] = None, rules_override: Optional[Dict[str, Any]] = None) -> None:
        self.rules_path = rules_path or Path(__file__).resolve().parents[2] / "contracts" / "validation_rules.yaml"
        self.rules_override = rules_override
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if self.rules_override is not None:
            if "rule_set" in self.rules_override:
                return self.rules_override.get("rule_set", {})
            return self.rules_override
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("rule_set", {})

    def execute(self, payload: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        normalized = dict(payload)
        meta = meta or {}

        global_rules = self.rules.get("global_rules", {})
        skill_rules = self.rules.get("skill_rules", {})
        policy = self.rules.get("output_policy", {})

        # Required fields
        for field in global_rules.get("required_fields", []):
            if field not in payload or payload.get(field) in (None, "", []):
                errors.append(f"missing_required_field:{field}")

        # Field types
        field_types = global_rules.get("field_types", {})
        if "test_item" in field_types and payload.get("test_item") is not None:
            if not isinstance(payload.get("test_item"), str):
                errors.append("invalid_type:test_item")
        if "test_unit" in field_types and payload.get("test_unit") is not None:
            if not isinstance(payload.get("test_unit"), str):
                errors.append("invalid_type:test_unit")
        if "test_result" in field_types and payload.get("test_result") is not None:
            if not isinstance(payload.get("test_result"), (int, float)):
                errors.append("invalid_type:test_result")
        if "evidence_refs" in field_types and payload.get("evidence_refs") is not None:
            if not isinstance(payload.get("evidence_refs"), list):
                errors.append("invalid_type:evidence_refs")

        # Evidence rules
        evidence_rules = global_rules.get("evidence_rules", {})
        evidence_refs = payload.get("evidence_refs") or []
        if len(evidence_refs) < evidence_rules.get("min_count", 0):
            errors.append("evidence_refs_too_few")

        # Confidence rules
        confidence = payload.get("confidence")
        if confidence is not None:
            warning_th = global_rules.get("confidence_rules", {}).get("warning_threshold", 0.7)
            error_th = global_rules.get("confidence_rules", {}).get("error_threshold", 0.4)
            if confidence < error_th:
                errors.append("confidence_too_low")
            elif confidence < warning_th:
                warnings.append("confidence_low")

        # Skill-specific rules
        test_item_val = payload.get("test_item")
        test_item = str(test_item_val) if test_item_val is not None else ""
        
        whitelist = skill_rules.get("test_item_whitelist", [])
        whitelist_mode = skill_rules.get("test_item_whitelist_mode", "error")
        if whitelist and test_item not in whitelist:
            if whitelist_mode == "warning":
                warnings.append("test_item_not_in_whitelist")
            else:
                errors.append("test_item_not_allowed")

        if meta.get("test_item_from_fallback"):
            warnings.append("test_item_fallback_from_node_label")

        # Record code vs node type warning
        record_code = None
        raw_result = payload.get("raw_result") if isinstance(payload.get("raw_result"), dict) else {}
        
        # 统一从 raw_result.meta 获取 control_code (优先) 或兼容旧路径
        if isinstance(raw_result, dict):
            # 兼容：meta 可能直接是 dict，或者 raw_result 本身
            meta_data = raw_result.get("meta") if isinstance(raw_result.get("meta"), dict) else {}
            record_code = (
                meta_data.get("control_code") 
                or raw_result.get("record_code") 
                or raw_result.get("记录编号")
            )

        test_value_json = payload.get("test_value_json")
        # 如果 raw_result 里没找到，尝试从 test_value_json 找
        if not record_code and isinstance(test_value_json, dict):
            record_code = test_value_json.get("control_code") or test_value_json.get("record_code")
            
        expected_type = resolve_expected_type(str(payload.get("node_id") or ""))
        
        # 使用新逻辑解析类型
        actual_record_spec = resolve_record_type(record_code)
        
        if record_code and actual_record_spec and expected_type:
            actual_type = actual_record_spec.business_type
            if actual_type != expected_type:
                # 生成带推断依据的警告
                warnings.append(
                    f"record_code_mismatch: code='{record_code}', "
                    f"inferred_type='{actual_record_spec.name}' ({actual_type}), "
                    f"expected_type='{expected_type}'"
                )

        unit_rules = skill_rules.get("unit_rules", {})
        normalize_map = unit_rules.get("normalize_map", {})
        unit = payload.get("test_unit")
        
        # Only validate unit rules if unit is a string (to avoid TypeError with unhashable types in sets/dicts)
        if isinstance(unit, str):
            if unit in normalize_map:
                normalized["test_unit"] = normalize_map[unit]
                unit = normalized["test_unit"]
            allowed_units = unit_rules.get("allowed_units", [])
            if allowed_units and unit not in allowed_units:
                errors.append("unit_not_allowed")

            semantic_rules = skill_rules.get("semantic_rules", {})
            forbid_units = set(semantic_rules.get("forbid_units", []))
            if unit in forbid_units:
                errors.append("unit_forbidden")
        else:
            # If unit is present but not a string, we already added "invalid_type:test_unit" error above
            semantic_rules = skill_rules.get("semantic_rules", {})

        for keyword in semantic_rules.get("forbid_keywords_in_test_item", []):
            if keyword and keyword in test_item:
                errors.append("test_item_forbidden_keyword")
                break

        # Value rules
        value_rules = skill_rules.get("value_rules", {})
        test_result = payload.get("test_result")
        if test_result is not None:
            if value_rules.get("non_negative") and test_result < 0:
                errors.append("test_result_negative")
            min_value = value_rules.get("min_value")
            max_value = value_rules.get("max_value")
            if min_value is not None and test_result < min_value:
                errors.append("test_result_too_small")
            if max_value is not None and test_result > max_value:
                errors.append("test_result_too_large")

        confirmed_meta = self._build_confirmed_meta(payload)
        if confirmed_meta:
            confirmed_result = payload.get("confirmed_result")
            confirmed_result = confirmed_result if isinstance(confirmed_result, dict) else {}
            confirmed_result_meta = confirmed_result.get("meta")
            confirmed_result_meta = confirmed_result_meta if isinstance(confirmed_result_meta, dict) else {}
            for key, value in confirmed_meta.items():
                if key not in confirmed_result_meta:
                    confirmed_result_meta[key] = value
            confirmed_result["meta"] = confirmed_result_meta
            normalized["confirmed_result"] = confirmed_result

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            normalized=normalized,
            policy=policy,
        )

    def _build_confirmed_meta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ruleset = self.rules.get("ruleset")
        if not ruleset:
            return {}

        def parse_date(value: Any) -> Optional[int]:
            if value is None:
                return None
            text = str(value).strip()
            if not text:
                return None
            parts = re.findall(r"\d{1,4}", text)
            if not parts:
                return None
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            day = int(parts[2]) if len(parts) > 2 else 1
            try:
                return year * 10000 + month * 100 + day
            except (TypeError, ValueError):
                return None

        def days_between(start: Any, end: Any) -> Optional[int]:
            start_val = parse_date(start)
            end_val = parse_date(end)
            if start_val is None or end_val is None:
                return None
            start_year = start_val // 10000
            start_month = (start_val // 100) % 100
            start_day = start_val % 100
            end_year = end_val // 10000
            end_month = (end_val // 100) % 100
            end_day = end_val % 100
            try:
                from datetime import date as dt_date
                return (dt_date(end_year, end_month, end_day) - dt_date(start_year, start_month, start_day)).days
            except (TypeError, ValueError):
                return None

        def parse_design_grade(value: Any) -> Optional[float]:
            if value is None:
                return None
            text = str(value).strip()
            if not text:
                return None
            if text.upper().startswith("C"):
                text = text[1:]
            try:
                return float(text)
            except ValueError:
                return None

        def as_number(value: Any) -> Optional[float]:
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        test_date = payload.get("test_date")
        casting_date = payload.get("casting_date")
        age_days = days_between(casting_date, test_date)

        carbonation = as_number(payload.get("carbonation_depth_avg_mm"))
        design_grade = payload.get("design_strength_grade") or payload.get("component_type")
        strength = as_number(payload.get("strength_estimated_mpa") or payload.get("test_result"))

        confirmed_meta: Dict[str, Any] = {
            "correction_standard_code": None,
            "correction_standard_name": None,
            "correction_ref": None,
            "strength_correction_factor": None,
            "result_evaluation_text": None,
        }

        if ruleset == "GB50292-2015-appendix-K":
            confirmed_meta["correction_standard_code"] = "GB50292-2015"
            confirmed_meta["correction_standard_name"] = "民用建筑可靠性鉴定标准"
            confirmed_meta["correction_ref"] = "附录K"
            if age_days is not None and carbonation is not None:
                if age_days > 1000 and carbonation > 6:
                    confirmed_meta["strength_correction_factor"] = 0.98

        design_value = parse_design_grade(design_grade)
        if strength is not None and design_value is not None:
            confirmed_meta["result_evaluation_text"] = (
                "符合设计要求" if strength >= design_value else "不符合设计要求"
            )

        # Remove empty keys
        return {k: v for k, v in confirmed_meta.items() if v is not None}
