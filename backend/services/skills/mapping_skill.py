from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class MappingSkill:
    """Map structured data into professional_data schema."""

    def __init__(self) -> None:
        self.prompt_version = "v1"
        self.schema_version = "v1"

    def execute(
        self,
        project_id: str,
        node_id: str,
        source_hash: str,
        structured_data: Any,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        run_id: Optional[str] = None,
        test_item_override: Optional[str] = None,
        mapping_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        record = self._pick_first_record(structured_data)
        mapping_config = mapping_override if mapping_override is not None else self._load_mapping_config(node_id)
        if "mapping" in mapping_config:
            mapping_config = mapping_config.get("mapping", {})

        if "test_item_normalization" in mapping_config:
            test_item_original = self._get_value(record, ["test_item", "检测项目", "test_item_original"]) or test_item_override or node_id
            test_item, test_item_source = self._normalize_test_item(mapping_config, test_item_original)
            test_item_from_fallback = test_item_source == "fallback"
            test_unit_original = self._get_value(record, ["test_unit", "单位", "强度单位", "test_unit_original"])
            test_unit, test_unit_source = self._normalize_unit(mapping_config, test_unit_original)
            test_result, test_result_source = self._parse_test_result(mapping_config, record)
            mapped_fields = {
                "test_result": test_result,
                "test_unit": test_unit,
                "component_type": self._get_str(record, ["设计强度等级"]),
                "location": self._get_value(record, ["检测部位"]),
                "test_value_json": {
                    "test_item_original": test_item_original,
                    "test_item_source": test_item_source,
                    "test_unit_original": test_unit_original,
                    "test_unit_source": test_unit_source,
                    "test_result_source": test_result_source,
                    "mapping_rule_set_id": mapping_config.get("meta", {}).get("rule_set_id"),
                },
            }
        else:
            test_item = mapping_config.get("test_item") or test_item_override or node_id
            test_item_from_fallback = mapping_config.get("test_item") is None and test_item_override is None
            mapped_fields = self._apply_mapping(mapping_config.get("fields", {}), record)
            test_result = mapped_fields.get("test_result")
            test_unit = mapped_fields.get("test_unit") or "MPa"

        control_code = self._extract_control_code(record)
        record_code = control_code or self._get_value_from_sources(
            record,
            [
                "record_code",
                "control_code",
                "控制编号",
                "记录编号",
            ],
        )
        test_location_text = self._get_str_from_sources(
            record,
            [
                "test_location_text",
                "test_location",
                "position",
                "检测部位",
                "抽测部位",
                "构件部位",
                "构件位置",
                "位置",
            ],
        )
        design_strength_grade = self._get_str_from_sources(
            record,
            [
                "design_strength_grade",
                "design_grade",
                "设计强度等级",
                "强度等级",
            ],
        )
        strength_estimated_mpa = self._get_numeric_from_sources(
            record,
            [
                "strength_estimated_mpa",
                "混凝土回弹推定强度",
                "回弹推定强度",
                "抗压强度推定值",
                "混凝土强度推定值_MPa",
                "混凝土强度推定值(MPa)",
                "混凝土强度推定值",
            ],
        )
        carbonation_depth_avg_mm = self._get_numeric_from_sources(
            record,
            [
                "carbonation_depth_avg_mm",
                "碳化深度平均值_mm",
                "碳化深度平均值",
            ],
        )
        test_date = self._normalize_date_text(
            self._get_value_from_sources(
                record,
                [
                    "test_date",
                    "test_date_raw",
                    "检测日期",
                    "测试日期",
                ],
            )
        )
        casting_date = self._normalize_date_text(
            self._get_value_from_sources(
                record,
                [
                    "casting_date",
                    "construction_date",
                    "construction_date_raw",
                    "施工日期",
                    "浇筑日期",
                ],
            )
        )
        if "test_value_json" not in mapped_fields or mapped_fields.get("test_value_json") is None:
            mapped_fields["test_value_json"] = {}
        if control_code:
            mapped_fields["test_value_json"]["control_code"] = control_code

        raw_result = structured_data if structured_data is not None else {}
        if isinstance(raw_result, dict):
            normalized_raw = dict(raw_result)
            meta = normalized_raw.get("meta")
            meta = dict(meta) if isinstance(meta, dict) else {}
            if control_code:
                meta.setdefault("control_code", control_code)
                meta.setdefault("control_code_source", "llm")
            concrete_type = self._get_str_from_sources(
                record,
                ["concrete_type", "混凝土类型", "混凝土类别", "concrete_kind"],
            )
            test_method = self._get_str_from_sources(
                record,
                ["test_method", "method", "检测方法", "检测方案"],
            )
            test_instrument = self._get_str_from_sources(
                record,
                ["test_instrument", "检测仪器", "检测设备"],
            )
            if concrete_type:
                meta.setdefault("concrete_type", concrete_type)
            if test_method:
                meta.setdefault("test_method", test_method)
            if test_instrument:
                meta.setdefault("test_instrument", test_instrument)
            if meta:
                normalized_raw["meta"] = meta
            raw_result = normalized_raw
        raw_hash = self._hash_json(raw_result)
        input_fingerprint = f"{source_hash}:{node_id}"

        payload = {
            "project_id": project_id,
            "node_id": node_id,
            "run_id": run_id,
            "test_item": test_item,
            "test_result": test_result,
            "test_unit": test_unit,
            "record_code": record_code,
            "test_location_text": test_location_text,
            "design_strength_grade": design_strength_grade,
            "strength_estimated_mpa": strength_estimated_mpa,
            "carbonation_depth_avg_mm": carbonation_depth_avg_mm,
            "test_date": test_date,
            "casting_date": casting_date,
            "test_value_json": mapped_fields.get("test_value_json"),
            "component_type": mapped_fields.get("component_type"),
            "location": mapped_fields.get("location"),
            "evidence_refs": evidence_refs or [],
            "raw_result": raw_result,
            "confirmed_result": None,
            "result_version": 1,
            "source_prompt_version": self.prompt_version,
            "schema_version": self.schema_version,
            "raw_hash": raw_hash,
            "input_fingerprint": input_fingerprint,
            "confirmed_by": None,
            "confirmed_at": None,
            "source_hash": source_hash,
            "confidence": None,
        }

        return {
            "mapped": payload,
            "meta": {
                "test_item_from_fallback": test_item_from_fallback,
            },
        }

    @staticmethod
    def _pick_first_record(data: Any) -> Dict[str, Any]:
        if isinstance(data, list):
            if len(data) == 0:
                return {}
            first = data[0]
            if isinstance(first, dict) and "structured_data" in first:
                return first.get("structured_data") or {}
            return first if isinstance(first, dict) else {}
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _extract_control_code(record: Dict[str, Any]) -> Optional[str]:
        if not isinstance(record, dict):
            return None
        for key in ("record_code", "控制编号", "记录编号", "control_code"):
            if key in record:
                return record.get(key)
        header = record.get("header")
        if isinstance(header, dict):
            for key in ("record_code", "控制编号", "记录编号", "control_code"):
                if key in header:
                    return header.get(key)
        return None

    @staticmethod
    def _get_value(record: Dict[str, Any], keys: List[str]) -> Any:
        for key in keys:
            if key in record:
                return record.get(key)
        return None

    @staticmethod
    def _get_str(record: Dict[str, Any], keys: List[str]) -> Optional[str]:
        value = MappingSkill._get_value(record, keys)
        return str(value) if value is not None else None

    @staticmethod
    def _get_numeric(record: Dict[str, Any], keys: List[str]) -> Optional[float]:
        value = MappingSkill._get_value(record, keys)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_value_from_sources(record: Dict[str, Any], keys: List[str]) -> Any:
        value = MappingSkill._get_value(record, keys)
        if value is not None:
            return value
        header = record.get("header") if isinstance(record, dict) else None
        if isinstance(header, dict):
            value = MappingSkill._get_value(header, keys)
            if value is not None:
                return value
        rows = record.get("rows") if isinstance(record, dict) else None
        if isinstance(rows, list) and rows:
            first_row = rows[0] if isinstance(rows[0], dict) else {}
            value = MappingSkill._get_value(first_row, keys)
            if value is not None:
                return value
        return None

    @staticmethod
    def _get_str_from_sources(record: Dict[str, Any], keys: List[str]) -> Optional[str]:
        value = MappingSkill._get_value_from_sources(record, keys)
        return str(value) if value is not None else None

    @staticmethod
    def _get_numeric_from_sources(record: Dict[str, Any], keys: List[str]) -> Optional[float]:
        value = MappingSkill._get_value_from_sources(record, keys)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_date_text(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        parts = re.findall(r"\\d{1,4}", text)
        if not parts:
            return None
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"

    @staticmethod
    def _hash_json(data: Any) -> str:
        encoded = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_mapping_config(self, node_id: str) -> Dict[str, Any]:
        mapping_dir = Path(__file__).resolve().parents[2] / "contracts" / "mapping"
        candidates = [
            mapping_dir / f"{node_id}.yaml",
            mapping_dir / f"{node_id}.yml",
            mapping_dir / "concrete_strength.yaml",
        ]
        for path in candidates:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
        return {}

    def _apply_mapping(self, fields: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
        output: Dict[str, Any] = {}
        for target, rule in fields.items():
            if "value" in rule:
                output[target] = rule["value"]
                continue
            source_keys = rule.get("source_keys", [])
            value = self._get_value(record, source_keys) if source_keys else None
            transform = rule.get("transform")
            output[target] = self._transform_value(value, transform)
        return output

    @staticmethod
    def _transform_value(value: Any, transform: Optional[str]) -> Any:
        if transform == "number":
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None
        if transform == "string":
            return str(value) if value is not None else None
        if transform == "json":
            return value
        return value

    def _normalize_test_item(self, config: Dict[str, Any], test_item_original: str) -> tuple[str, str]:
        rules = config.get("test_item_normalization", {})
        for item in rules.get("canonical_items", []):
            if self._match_item(test_item_original, item.get("aliases_exact", []), item.get("aliases_regex", [])):
                return item.get("canonical_value"), "mapped"
        fallback = rules.get("fallback", {})
        if fallback.get("use_node_label_as_test_item"):
            return test_item_original, "fallback"
        return test_item_original, "original"

    def _normalize_unit(self, config: Dict[str, Any], unit_original: Optional[str]) -> tuple[Optional[str], str]:
        rules = config.get("unit_normalization", {})
        canonical_units = rules.get("canonical_units", {})
        if unit_original:
            for canonical, unit_rules in canonical_units.items():
                if self._match_item(unit_original, unit_rules.get("aliases_exact", []), unit_rules.get("aliases_regex", [])):
                    return canonical, "mapped"
            return unit_original, "original"

        infer = rules.get("infer_if_missing", {})
        if infer.get("enabled"):
            return infer.get("default_unit"), "inferred"
        return None, "missing"

    def _parse_test_result(self, config: Dict[str, Any], record: Dict[str, Any]) -> tuple[Optional[float], str]:
        raw = self._get_value(
            record,
            [
                "混凝土强度推定值_MPa",
                "混凝土强度推定值（MPa）",
                "混凝土强度推定值(MPa)",
                "回弹推定强度",
                "混凝土回弹推定强度",
                "混凝土强度推定值",
                "强度推定值",
                "推定值",
                "test_result",
            ],
        )
        if raw is None:
            return None, "missing"

        if isinstance(raw, (int, float)):
            return float(raw), "original"

        text_value = str(raw)
        parsing = config.get("value_parsing", {})
        for token in parsing.get("strip_tokens", []):
            text_value = text_value.replace(token, "")
        if parsing.get("extract_number_from_string", {}).get("enabled"):
            pattern = parsing.get("extract_number_from_string", {}).get("regex")
            match = re.search(pattern, text_value)
            if match:
                try:
                    return float(match.group(1)), "parsed"
                except (TypeError, ValueError):
                    return None, "invalid"
        try:
            return float(text_value), "parsed"
        except (TypeError, ValueError):
            return None, "invalid"

    @staticmethod
    def _match_item(value: str, exact_list: List[str], regex_list: List[str]) -> bool:
        if value in exact_list:
            return True
        for item in exact_list:
            if value.lower() == str(item).lower():
                return True
        for pattern in regex_list:
            try:
                if re.search(pattern, value):
                    return True
            except re.error:
                continue
        return False
