# -*- coding: utf-8 -*-
from __future__ import annotations


from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

import yaml

from models.db import fetch_professional_data


@dataclass
class ChapterResult:
    chapter_id: str
    title: str
    template_style: str
    reference_spec_type: str
    reference_spec: str
    blocks: List[Dict[str, Any]]
    summary: Dict[str, Any]
    evidence_refs: List[Dict[str, Any]]


class ChapterGenerationSkill:
    """Generate chapter JSON from professional_data records."""

    TABLE7_COLUMNS = [
        {"key": "index", "label": "序号"},
        {"key": "position", "label": "抽测部位"},
        {"key": "design_grade", "label": "抗压强度设计值"},
        {"key": "strength_estimated_mpa", "label": "龄期修正后混凝土抗压强度推定值(MPa)"},
        {"key": "carbonation_depth_avg_mm", "label": "碳化深度平均值(mm)"},
        {"key": "evaluation", "label": "抽测结果评价"},
    ]
    RECORD_SHEET_COLUMNS = [
        {"key": "index", "label": "序号"},
        {"key": "position", "label": "构件部位"},
        {"key": "surface_state", "label": "表面状态"},
        {"key": "design_grade", "label": "强度等级"},
        {"key": "construction_date", "label": "施工日期"},
        {"key": "assessment_type", "label": "判定类型"},
    ]
    DEFAULT_EMPTY_MESSAGE = "未找到符合条件的回弹法混凝土抗压强度记录"
    DESCRIPTION_PROMPT = (
        "你是工程报告文本生成助手。请仅基于给定事实生成简洁中文描述，"
        "不得引入任何未提供的数据，不得进行计算或推断。"
    )
    RULES_DIR = Path(__file__).resolve().parents[2] / "contracts" / "rules"

    def _extract_method(self, test_value_json: Dict[str, Any], raw_result: Dict[str, Any]) -> Optional[str]:
        return (
            test_value_json.get("test_method")
            or raw_result.get("test_method")
            or raw_result.get("method")
        )

    def _build_location_display(self, location: Any) -> str:
        if isinstance(location, str):
            return location or "未标注"
        if not isinstance(location, dict):
            return "未标注"
        display = location.get("display")
        if display:
            return display
        parts = [
            location.get("floor"),
            location.get("axis"),
            location.get("member"),
            location.get("test_zone"),
        ]
        return " ".join([p for p in parts if p]) or "未标注"

    def _ensure_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _as_number(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _normalize_method(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return value.replace(" ", "").strip()

    def _format_number(self, value: Optional[float], digits: int) -> str:
        if value is None:
            return ""
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")

    def _format_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)

    def _normalize_date_text(self, value: Any) -> Optional[str]:
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

    def _parse_date_value(self, value: Any) -> Optional[date]:
        text = self._normalize_date_text(value)
        if not text:
            return None
        try:
            year, month, day = [int(part) for part in text.split("-")]
            return date(year, month, day)
        except (TypeError, ValueError):
            return None

    def _most_common_text(self, values: List[str]) -> Optional[str]:
        cleaned = [value for value in values if isinstance(value, str) and value.strip()]
        if not cleaned:
            return None
        counts: Dict[str, int] = {}
        for value in cleaned:
            counts[value] = counts.get(value, 0) + 1
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _build_strength_description_text(self, facts: Dict[str, Any], table_ref: str) -> str:
        parts: List[str] = []
        concrete_type = facts.get("concrete_type")
        test_method = facts.get("test_method") or "回弹法"
        test_instrument = facts.get("test_instrument")
        sample_scope = facts.get("sample_scope") or "混凝土构件"

        intro = f"鉴定对象采用{concrete_type or '混凝土'}，现场采用"
        if test_instrument:
            intro += f"{test_instrument}"
        intro += f"对{sample_scope}强度进行抽测"
        parts.append(intro)

        if facts.get("age_days_over_1000") is True:
            parts.append("由于混凝土龄期已超过1000天")

        if facts.get("carbonation_depth_over_6") is True:
            parts.append("碳化深度均大于6mm")

        correction_standard = facts.get("correction_standard")
        correction_factor = facts.get("strength_correction_factor")
        if correction_standard or correction_factor:
            correction_text = "依据"
            correction_text += correction_standard or "相关规范"
            correction_text += "进行修正"
            if correction_factor is not None:
                correction_text += f"，混凝土强度修正系数取{correction_factor}"
            parts.append(correction_text)

        if table_ref:
            parts.append(f"抽测结果见{table_ref}")

        min_strength = facts.get("strength_min_mpa")
        design_grade = facts.get("design_strength_grade")
        evaluation = facts.get("evaluation")
        if min_strength is not None:
            tail = f"由上表可知，抽测的混凝土构件抗压强度最小值为{min_strength}MPa"
            if design_grade:
                tail += f"，符合设计{design_grade}强度等级要求"
            if evaluation:
                tail += f"（{evaluation}）"
            parts.append(tail)

        return "，".join([part for part in parts if part]) + "。"

    def _parse_design_grade(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if text.upper().startswith("C"):
            text = text[1:]
        try:
            return float(text)
        except ValueError:
            return None

    def _compute_evaluation(self, strength: Optional[float], design_grade: Any) -> Optional[str]:
        if strength is None:
            return None
        design_value = self._parse_design_grade(design_grade)
        if design_value is None:
            return None
        return "符合设计要求" if strength >= design_value else "不符合设计要求"

    def _resolve_rule_id(self, rule_key: Optional[str]) -> Optional[str]:
        if not rule_key:
            return None
        rule_key = str(rule_key).strip()
        rule_map = {
            "混凝土强度 v1.0": "concrete_strength_v1",
            "混凝土强度v1.0": "concrete_strength_v1",
            "concrete_strength_v1": "concrete_strength_v1",
        }
        return rule_map.get(rule_key, None)

    def _load_rule(self, rule_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not rule_id:
            return None
        rule_path = self.RULES_DIR / f"{rule_id}.yaml"
        if not rule_path.exists():
            return None
        with rule_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def _apply_rule_evaluation(
        self,
        strength: Optional[float],
        design_grade: Any,
        rule: Dict[str, Any],
    ) -> Optional[str]:
        if rule is None:
            return None
        if design_grade is None or str(design_grade).strip() == "":
            for constraint in rule.get("constraints", []):
                if constraint.get("id") == "missing_design_grade":
                    return constraint.get("then", {}).get("evaluation")
            return None
        design_value = self._parse_design_grade(design_grade)
        if design_value is None or strength is None:
            return None
        rule_block = (rule.get("rules") or [{}])[0]
        then_eval = rule_block.get("then", {}).get("evaluation")
        else_eval = rule_block.get("else", {}).get("evaluation")
        return then_eval if strength >= design_value else else_eval

    def _dedupe_evidence(self, refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        result: List[Dict[str, Any]] = []
        for ref in refs:
            ref_value = ref.get("ref") or ref.get("object_key")
            if not ref_value:
                result.append(ref)
                continue
            key = (ref.get("type"), ref_value)
            if key in seen:
                continue
            seen.add(key)
            result.append(ref)
        return result

    def _resolve_dataset(self, dataset_key: str) -> Dict[str, Any]:
        if dataset_key == "concrete_rebound_tests":
            return {
                "test_items": ["混凝土抗压强度", "混凝土强度"],
                "method_keyword": "回弹",
                "table_id": "table_7_rebound",
                "title": "表7 回弹法检测结果汇总",
                "columns": self.TABLE7_COLUMNS,
                "strength_digits": 1,
                "carbonation_digits": 0,
                "allow_empty_method": True,
                "empty_message": self.DEFAULT_EMPTY_MESSAGE,
            }
        if dataset_key == "concrete_rebound_record_sheet":
            return {
                "header_item": "混凝土回弹检测-元信息",
                "row_item": "混凝土回弹检测-原始记录",
                "table_id": "table_rebound_record_sheet_v1",
                "title": "回弹法检测原始记录汇总",
                "columns": self.RECORD_SHEET_COLUMNS,
                "empty_message": "未找到符合条件的回弹检测原始记录",
            }
        if dataset_key == "concrete_strength_description":
            return {
                "output_type": "text",
                "table_ref": "表7",
            }
        raise ValueError(f"Unsupported dataset_key: {dataset_key}")

    def _generate_record_sheet(
        self,
        project_id: str,
        node_id: str,
        dataset: Dict[str, Any],
    ) -> Dict[str, Any]:
        header_records = fetch_professional_data(
            project_id=project_id,
            node_id=node_id,
            test_item=dataset["header_item"],
        )
        detail_records = fetch_professional_data(
            project_id=project_id,
            node_id=node_id,
            test_item=dataset["row_item"],
        )

        header = header_records[0] if header_records else {}
        header_raw = self._ensure_dict(header.get("raw_result"))
        header_test_value = self._ensure_dict(header.get("test_value_json"))

        test_date_raw = (
            header_raw.get("test_date")
            or header_raw.get("检测日期")
            or header_test_value.get("test_date")
        )
        assessment_type = header_raw.get("assessment_type") or header_raw.get("评定类型")
        test_date = self._normalize_date_text(test_date_raw)

        rows: List[Dict[str, Any]] = []
        evidence_refs: List[Dict[str, Any]] = []

        for record in detail_records:
            raw_result = self._ensure_dict(record.get("raw_result"))
            location = record.get("location")
            position = record.get("test_location_text") or self._build_location_display(location)
            if position == "未标注":
                position = raw_result.get("构件部位") or raw_result.get("检测部位") or position

            surface_state = raw_result.get("surface_state") or raw_result.get("表面状态")
            design_grade = (
                record.get("design_strength_grade")
                or raw_result.get("design_grade")
                or raw_result.get("强度等级")
                or record.get("component_type")
            )
            construction_raw = (
                record.get("casting_date")
                or raw_result.get("construction_date")
                or raw_result.get("construction_date_raw")
                or raw_result.get("施工日期")
            )
            construction_date = self._normalize_date_text(construction_raw)
            row_assessment = (
                raw_result.get("assessment_type")
                or raw_result.get("评定类型")
                or assessment_type
            )

            rows.append(
                {
                    "position": position,
                    "surface_state": surface_state,
                    "design_grade": design_grade,
                    "construction_date": construction_date,
                    "assessment_type": row_assessment,
                }
            )

            evidence_refs.extend(record.get("evidence_refs") or [])
        if header:
            evidence_refs.extend(header.get("evidence_refs") or [])

        rows.sort(key=lambda item: item.get("position") or "")

        table_rows = []
        for idx, row in enumerate(rows, start=1):
            table_rows.append(
                {
                    "index": idx,
                    "position": self._format_text(row.get("position")),
                    "surface_state": self._format_text(row.get("surface_state")),
                    "design_grade": self._format_text(row.get("design_grade")),
                    "construction_date": self._format_text(row.get("construction_date")),
                    "assessment_type": self._format_text(row.get("assessment_type")),
                }
            )

        summary = {
            "test_date": self._format_text(test_date),
            "assessment_type": self._format_text(assessment_type),
            "record_count": len(table_rows),
        }

        blocks: List[Dict[str, Any]] = []
        if not table_rows:
            blocks.append(
                {
                    "type": "note",
                    "text": dataset["empty_message"],
                }
            )
        blocks.append(
            {
                "type": "table",
                "table_id": dataset["table_id"],
                "title": dataset["title"],
                "columns": dataset["columns"],
                "rows": table_rows,
            }
        )

        return {
            "blocks": blocks,
            "summary": summary,
            "evidence_refs": self._dedupe_evidence(evidence_refs),
        }

    def _generate_strength_description(
        self,
        project_id: str,
        node_id: Optional[str],
        dataset: Dict[str, Any],
        chapter_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        use_confirmed_result = bool(chapter_config.get("use_confirmed_result", True))
        ruleset = chapter_config.get("ruleset")
        records = fetch_professional_data(
            project_id=project_id,
            node_id=node_id,
            test_item=None,
        )

        CARBONATION_THRESHOLD = 6

        evidence_refs: List[Dict[str, Any]] = []
        facts_used: Dict[str, Any] = {}
        rules_fired: List[str] = []

        def pick_value(record: Dict[str, Any], chain: List[str]) -> tuple[Optional[Any], Optional[str]]:
            for key in chain:
                if "." in key:
                    parts = key.split(".")
                    value: Any = record
                    ok = True
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value.get(part)
                        else:
                            ok = False
                            break
                    if ok and value not in (None, "", []):
                        return value, key
                else:
                    if key in record and record.get(key) not in (None, "", []):
                        return record.get(key), key
            return None, None

        def pick_number(record: Dict[str, Any], chain: List[str]) -> tuple[Optional[float], Optional[str]]:
            value, source = pick_value(record, chain)
            number = self._as_number(value)
            if number is None:
                return None, None
            return number, source

        def extract_grade(value: Any) -> Optional[str]:
            if value is None:
                return None
            text = str(value).strip()
            if not text:
                return None
            match = re.search(r"(C\\d{2})", text.upper())
            if match:
                return match.group(1)
            return text

        field_chains = {
            "method": ["raw_result.meta.test_method", "raw_result.test_method", "raw_result.method"],
            "strength_value_mpa": ["strength_estimated_mpa", "raw_result.strength_estimated_mpa", "test_result"],
            "carbonation_depth_avg_mm": ["carbonation_depth_avg_mm", "raw_result.carbonation_depth_avg_mm"],
            "test_date": ["test_date", "raw_result.test_date"],
            "casting_date": ["casting_date", "raw_result.construction_date"],
            "design_grade": ["design_strength_grade", "component_type"],
        }

        table_strengths: List[float] = []
        table_design_grades: List[str] = []
        table_dataset = self._resolve_dataset("concrete_rebound_tests")
        table_allow_empty_method = bool(table_dataset.get("allow_empty_method", False))

        concrete_types: List[str] = []
        methods: List[str] = []
        instruments: List[str] = []
        design_grades: List[str] = []
        strengths: List[float] = []
        carbonation_values: List[float] = []
        test_dates: List[date] = []
        casting_dates: List[date] = []
        correction_standards: List[str] = []
        correction_factors: List[float] = []
        evaluation_texts: List[str] = []
        source_counter: Dict[str, Dict[str, int]] = {key: {} for key in field_chains}

        for record in records:
            raw_result = self._ensure_dict(record.get("raw_result"))
            raw_meta = self._ensure_dict(raw_result.get("meta"))
            test_value_json = self._ensure_dict(record.get("test_value_json"))
            confirmed_result = (
                self._ensure_dict(record.get("confirmed_result")) if use_confirmed_result else {}
            )
            confirmed_meta = (
                self._ensure_dict(confirmed_result.get("meta")) if use_confirmed_result else {}
            )
            concrete_type = raw_meta.get("concrete_type")
            if concrete_type:
                concrete_types.append(str(concrete_type))

            method_value, method_source = pick_value(record, field_chains["method"])
            if method_value:
                methods.append(str(method_value))
                if method_source:
                    source_counter["method"][method_source] = source_counter["method"].get(method_source, 0) + 1

            instrument_value = raw_meta.get("test_instrument")
            if instrument_value:
                instruments.append(str(instrument_value))

            correction_standard = (
                confirmed_meta.get("correction_standard_code")
                or confirmed_meta.get("correction_standard_name")
                or confirmed_meta.get("correction_ref")
            )
            if correction_standard:
                correction_standards.append(str(correction_standard))
            correction_factor = confirmed_meta.get("strength_correction_factor")
            if correction_factor is not None:
                try:
                    correction_factors.append(float(correction_factor))
                except (TypeError, ValueError):
                    pass
            evaluation_value = (
                confirmed_meta.get("result_evaluation")
                or confirmed_meta.get("evaluation_status")
                or confirmed_meta.get("result_evaluation_text")
            )
            if evaluation_value:
                evaluation_texts.append(str(evaluation_value))

            grade_value, grade_source = pick_value(record, field_chains["design_grade"])
            grade_value = extract_grade(grade_value)
            if grade_value:
                design_grades.append(str(grade_value))
                if grade_source:
                    source_counter["design_grade"][grade_source] = source_counter["design_grade"].get(grade_source, 0) + 1

            strength_value, strength_source = pick_number(record, field_chains["strength_value_mpa"])
            if strength_value is not None:
                strengths.append(strength_value)
                if strength_source:
                    source_counter["strength_value_mpa"][strength_source] = source_counter["strength_value_mpa"].get(strength_source, 0) + 1

            carbonation_value, carbonation_source = pick_number(record, field_chains["carbonation_depth_avg_mm"])
            if carbonation_value is not None:
                carbonation_values.append(carbonation_value)
                if carbonation_source:
                    source_counter["carbonation_depth_avg_mm"][carbonation_source] = source_counter["carbonation_depth_avg_mm"].get(carbonation_source, 0) + 1

            test_date_value, test_date_source = pick_value(record, field_chains["test_date"])
            test_date = self._parse_date_value(test_date_value)
            if test_date:
                test_dates.append(test_date)
                if test_date_source:
                    source_counter["test_date"][test_date_source] = source_counter["test_date"].get(test_date_source, 0) + 1

            casting_date_value, casting_date_source = pick_value(record, field_chains["casting_date"])
            casting_date = self._parse_date_value(casting_date_value)
            if casting_date:
                casting_dates.append(casting_date)
                if casting_date_source:
                    source_counter["casting_date"][casting_date_source] = source_counter["casting_date"].get(casting_date_source, 0) + 1

            evidence_refs.extend(record.get("evidence_refs") or [])

            if record.get("test_item") in table_dataset.get("test_items", []):
                method = self._normalize_method(self._extract_method(test_value_json, raw_result))
                if method or table_allow_empty_method:
                    if not method or table_dataset["method_keyword"] in method:
                        table_strength = (
                            self._as_number(record.get("strength_estimated_mpa"))
                            or self._as_number(raw_result.get("strength_estimated_mpa"))
                            or self._as_number(record.get("test_result"))
                        )
                        if table_strength is not None:
                            table_strengths.append(table_strength)
                        table_grade = (
                            record.get("design_strength_grade")
                            or test_value_json.get("design_grade")
                            or raw_result.get("design_grade")
                            or raw_result.get("设计强度等级")
                            or record.get("component_type")
                        )
                        if table_grade:
                            table_design_grades.append(str(table_grade))

        def summarize_sources(field_key: str) -> Optional[str]:
            candidates = source_counter.get(field_key) or {}
            if not candidates:
                return None
            return sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[0][0]

        for key, chain in field_chains.items():
            facts_used[key] = {
                "chain": chain,
                "source": summarize_sources(key),
            }

        common_concrete_type = self._most_common_text(concrete_types)
        common_method = self._most_common_text(methods)
        common_instrument = self._most_common_text(instruments)
        common_design_grade = self._most_common_text(table_design_grades) or self._most_common_text(design_grades)

        strength_source = table_strengths if table_strengths else strengths
        strength_min = round(min(strength_source), 1) if strength_source else None
        strength_avg = round(sum(strength_source) / len(strength_source), 1) if strength_source else None
        strength_count = len(strength_source)
        carbonation_avg = round(sum(carbonation_values) / len(carbonation_values), 1) if carbonation_values else None

        age_days_value = None
        if test_dates and casting_dates:
            test_date = min(test_dates)
            casting_date = min(casting_dates)
            delta_days = (test_date - casting_date).days
            if delta_days >= 0:
                age_days_value = delta_days

        correction_standard = self._most_common_text(correction_standards) or ruleset
        correction_factor = None
        if correction_factors:
            correction_factor = round(sum(correction_factors) / len(correction_factors), 2)
        evaluation_text = self._most_common_text(evaluation_texts)

        test_date_for_fact = min(test_dates) if test_dates else None
        casting_date_for_fact = min(casting_dates) if casting_dates else None

        facts: Dict[str, Any] = {
            "concrete_type": common_concrete_type,
            "method": common_method,
            "instrument": common_instrument,
            "design_grade": common_design_grade,
            "strength_value_mpa": strength_min if strength_min is not None else strength_avg,
            "strength_stat": {
                "min_mpa": strength_min,
                "avg_mpa": strength_avg,
                "n": strength_count,
            },
            "carbonation_depth_avg_mm": carbonation_avg,
            "test_date": self._normalize_date_text(test_date_for_fact) if test_date_for_fact else None,
            "casting_date": self._normalize_date_text(casting_date_for_fact) if casting_date_for_fact else None,
            "age_days": age_days_value,
            "correction": {
                "standard": correction_standard,
                "factor": correction_factor,
                "eval_text": evaluation_text,
            },
            "sample_scope": chapter_config.get("sample_scope") or "混凝土构件",
            "evidence_refs": self._dedupe_evidence(evidence_refs),
        }

        if age_days_value is not None and age_days_value > 1000:
            rules_fired.append("age_days_over_1000")
        if carbonation_avg is not None and carbonation_avg >= CARBONATION_THRESHOLD:
            rules_fired.append("carbonation_over_threshold")

        def render_description_text(facts_data: Dict[str, Any], table_ref_value: str) -> str:
            sentences: List[str] = []
            concrete_type = facts_data.get("concrete_type") or "混凝土"
            method_text = facts_data.get("instrument") or facts_data.get("method")
            sample_scope = facts_data.get("sample_scope") or "混凝土构件"
            if method_text:
                sentences.append(
                    f"鉴定对象采用{concrete_type}，现场采用{method_text}对{sample_scope}强度进行抽测。"
                )
            else:
                sentences.append(
                    f"鉴定对象采用{concrete_type}，对{sample_scope}强度进行抽测。"
                )

            condition_parts: List[str] = []
            if facts_data.get("age_days") is not None:
                condition_parts.append(f"由于混凝土龄期已超过{facts_data.get('age_days')}天")
            if facts_data.get("carbonation_depth_avg_mm") is not None:
                if facts_data.get("carbonation_depth_avg_mm") >= CARBONATION_THRESHOLD:
                    condition_parts.append(f"碳化深度均大于{CARBONATION_THRESHOLD}mm")
                else:
                    condition_parts.append(f"碳化深度平均值为{facts_data.get('carbonation_depth_avg_mm')}mm")

            correction = facts_data.get("correction") or {}
            correction_parts: List[str] = []
            if correction.get("standard"):
                correction_parts.append(f"依据{correction.get('standard')}进行修正")
            if correction.get("factor") is not None:
                correction_parts.append(f"混凝土强度修正系数取{correction.get('factor')}")
            if table_ref_value:
                correction_parts.append(f"抽测结果见{table_ref_value}")

            middle_sentence = "，".join([part for part in condition_parts + correction_parts if part])
            if middle_sentence:
                sentences.append(middle_sentence + "。")

            strength_stat = facts_data.get("strength_stat") or {}
            min_mpa = strength_stat.get("min_mpa")
            value_mpa = min_mpa if min_mpa is not None else facts_data.get("strength_value_mpa")
            design_grade = facts_data.get("design_grade")
            if value_mpa is not None and design_grade:
                design_value = self._parse_design_grade(design_grade)
                evaluation = correction.get("eval_text")
                if evaluation is None and design_value is not None:
                    evaluation = "符合设计要求" if value_mpa >= design_value else "不符合设计要求"
                if evaluation is None:
                    evaluation = ""
                sentences.append(
                    f"由{table_ref_value or '抽测数据'}可知，抽测的混凝土构件抗压强度最小值为{value_mpa}MPa，{evaluation}。"
                )
            elif value_mpa is not None:
                sentences.append(
                    f"抽测的混凝土抗压强度为{value_mpa}MPa。"
                )

            return "".join(sentences)

        table_ref = chapter_config.get("table_ref") or dataset.get("table_ref") or "表7"
        description_text = render_description_text(facts, table_ref)

        blocks = [
            {
                "type": "text",
                "text": description_text,
                "facts": facts,
                "facts_used": facts_used,
                "rules_fired": rules_fired,
            }
        ]

        return {
            "blocks": blocks,
            "summary": facts,
            "evidence_refs": self._dedupe_evidence(evidence_refs),
        }

    def execute(self, project_id: str, chapter_config: Dict[str, Any]) -> ChapterResult:
        node_id = chapter_config.get("node_id") or chapter_config.get("chapter_id") or "chapter"
        title = chapter_config.get("title") or chapter_config.get("label") or "章节"
        template_style = chapter_config.get("template_style") or "text_table_1"
        reference_spec_type = chapter_config.get("reference_spec_type") or "system"
        reference_spec = chapter_config.get("reference_spec") or "JGJ/T 23-2011"
        dataset_key = chapter_config.get("dataset_key") or "concrete_rebound_tests"
        dataset = self._resolve_dataset(dataset_key)
        allow_empty_method = bool(
            chapter_config.get("allow_empty_method", dataset.get("allow_empty_method", False))
        )
        rule_id = self._resolve_rule_id(chapter_config.get("rule_id"))
        rule_config = self._load_rule(rule_id)
        source_node_id = chapter_config.get("sourceNodeId")
        aggregation_scope = chapter_config.get("aggregation_scope") or "project"
        if aggregation_scope == "project":
            query_node_id = None
        elif source_node_id:
            query_node_id = source_node_id
        else:
            query_node_id = node_id

        if dataset_key == "concrete_strength_description":
            result = self._generate_strength_description(project_id, query_node_id, dataset, chapter_config)
            return ChapterResult(
                chapter_id=node_id,
                title=title,
                template_style=template_style,
                reference_spec_type=reference_spec_type,
                reference_spec=reference_spec,
                blocks=result["blocks"],
                summary=result["summary"],
                evidence_refs=result["evidence_refs"],
            )

        if dataset_key == "concrete_rebound_record_sheet":
            result = self._generate_record_sheet(project_id, query_node_id, dataset)
            return ChapterResult(
                chapter_id=node_id,
                title=title,
                template_style=template_style,
                reference_spec_type=reference_spec_type,
                reference_spec=reference_spec,
                blocks=result["blocks"],
                summary=result["summary"],
                evidence_refs=result["evidence_refs"],
            )
        # Data source scoped by node_id; test_item filtered in memory.
        query_test_item = None

        records = fetch_professional_data(
            project_id=project_id,
            node_id=query_node_id,
            test_item=query_test_item,
        )

        rows: List[Dict[str, Any]] = []
        evidence_refs: List[Dict[str, Any]] = []
        strengths: List[float] = []
        design_grades: List[str] = []

        for record in records:
            if record.get("test_item") not in dataset["test_items"]:
                continue

            test_value_json = record.get("test_value_json") or {}
            raw_result = record.get("raw_result") or {}

            method = self._normalize_method(self._extract_method(test_value_json, raw_result))
            if not method and not allow_empty_method:
                continue
            if method and dataset["method_keyword"] not in method:
                continue

            location = record.get("location")
            design_grade = (
                record.get("design_strength_grade")
                or test_value_json.get("design_grade")
                or raw_result.get("design_grade")
                or raw_result.get("设计强度等级")
                or record.get("component_type")
            )
            strength = (
                self._as_number(record.get("strength_estimated_mpa"))
                or self._as_number(raw_result.get("strength_estimated_mpa"))
                or self._as_number(raw_result.get("混凝土强度推定值_MPa"))
                or self._as_number(record.get("test_result"))
            )
            carbonation = (
                self._as_number(record.get("carbonation_depth_avg_mm"))
                or self._as_number(raw_result.get("carbonation_depth_avg_mm"))
                or self._as_number(raw_result.get("碳化深度平均值_mm"))
                or self._as_number(raw_result.get("碳化深度平均值"))
            )
            evaluation = raw_result.get("evaluation") or raw_result.get("抽测结果评价")
            if not evaluation:
                evaluation = self._apply_rule_evaluation(strength, design_grade, rule_config)
            if not evaluation:
                evaluation = self._compute_evaluation(strength, design_grade)

            if design_grade:
                design_grades.append(str(design_grade))
            if strength is not None:
                strengths.append(strength)

            rows.append(
                {
                    "position": record.get("test_location_text") or self._build_location_display(location),
                    "design_grade": design_grade,
                    "strength_estimated_mpa": strength,
                    "carbonation_depth_avg_mm": carbonation,
                    "evaluation": evaluation,
                }
            )

            evidence_refs.extend(record.get("evidence_refs") or [])

        rows.sort(key=lambda item: item.get("position") or "")

        table_rows = []
        for idx, row in enumerate(rows, start=1):
            table_rows.append(
                {
                    "index": idx,
                    "position": self._format_text(row.get("position")),
                    "design_grade": self._format_text(row.get("design_grade")),
                    "strength_estimated_mpa": self._format_number(
                        row.get("strength_estimated_mpa"),
                        dataset["strength_digits"],
                    ),
                    "carbonation_depth_avg_mm": self._format_number(
                        row.get("carbonation_depth_avg_mm"),
                        dataset["carbonation_digits"],
                    ),
                    "evaluation": self._format_text(row.get("evaluation")),
                }
            )

        min_strength = min(strengths) if strengths else None
        design_grade = None
        if design_grades:
            grade_counts: Dict[str, int] = {}
            for grade in design_grades:
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            design_grade = sorted(grade_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        summary = {
            "min_strength_estimated_mpa": self._format_number(min_strength, dataset["strength_digits"]),
            "design_grade": design_grade,
        }
        if rule_config:
            summary["evaluation_rule"] = {
                "rule_id": rule_config.get("rule_id") or rule_id,
                "version": rule_config.get("version"),
            }

        blocks: List[Dict[str, Any]] = []
        if not table_rows:
            blocks.append(
                {
                    "type": "note",
                    "text": dataset["empty_message"],
                }
            )
        blocks.append(
            {
                "type": "table",
                "table_id": chapter_config.get("table_id") or dataset["table_id"],
                "title": dataset["title"],
                "columns": dataset["columns"],
                "rows": table_rows,
            }
        )

        return ChapterResult(
            chapter_id=node_id,
            title=title,
            template_style=template_style,
            reference_spec_type=reference_spec_type,
            reference_spec=reference_spec,
            blocks=blocks,
            summary=summary,
            evidence_refs=self._dedupe_evidence(evidence_refs),
        )
