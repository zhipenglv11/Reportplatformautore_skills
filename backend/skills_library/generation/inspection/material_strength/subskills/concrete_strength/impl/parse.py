"""
Concrete Strength Sub-Skill - 数据解析与生成
专门负责混凝土强度检测描述
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def parse_concrete_strength(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    解析混凝土强度数据并生成描述
    
    Args:
        project_id: 项目ID
        node_id: 节点ID
        context: 上下文配置
    
    Returns:
        结构化的混凝土强度描述数据
    """
    # 1. 从数据库读取混凝土数据
    records = await _fetch_concrete_data(project_id, node_id)
    
    if not records:
        logger.info(f"Project {project_id}, Node {node_id}: 未找到混凝土强度数据")
        return {
            "dataset_key": "concrete_strength",
            "content": "",
            "table": {"columns": [], "rows": []},
            "meta": {
                "source": "legacy_merge",
                "material_type": "concrete",
                "has_data": False,
                "warnings": ["未找到混凝土强度数据"]
            }
        }
    
    # 2. 提取字段数据
    parsed_data = _extract_fields(records)
    
    # 3. 验证数据
    validation = _validate_data(parsed_data)
    if validation["warnings"]:
        logger.warning(f"混凝土数据验证警告: {validation['warnings']}")
    
    # 4. 生成描述文字（段落文本）
    content_text = _generate_content_text(parsed_data, context or {})
    
    # 5. 返回统一格式：dataset_key + content + table + meta
    return {
        "dataset_key": "concrete_strength",
        "content": content_text,
        "table": parsed_data["table"],
        "meta": {
            "source": "legacy_merge",
            "material_type": "concrete",
            "title": "混凝土强度",
            "test_count": parsed_data["test_count"],
            "test_method": parsed_data["test_method"],
            "avg_strength": parsed_data["avg_strength"],
            "strength_range": parsed_data.get("strength_range"),
            "strength_grade": parsed_data.get("strength_grade"),
            "carbonation_depth": parsed_data.get("carbonation_depth"),
            "strength_unit": "MPa",
            "evidence_refs": parsed_data["evidence_refs"],
            "record_ids": parsed_data["record_ids"],
            "summary": parsed_data["summary"],
            "warnings": validation["warnings"],
            "skill_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "record_count": len(records)
        }
    }


async def _fetch_concrete_data(project_id: str, node_id: str) -> List[Dict[str, Any]]:
    """从professional_data表获取混凝土数据"""
    from models.db import get_engine
    from sqlalchemy import text
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        id,
                        test_item,
                        test_result,
                        strength_estimated_mpa,
                        design_strength_grade,
                        carbonation_depth_avg_mm,
                        test_date,
                        test_location_text,
                        raw_result,
                        confirmed_result,
                        evidence_refs
                    FROM professional_data
                    WHERE project_id = :pid
                    AND (
                        test_item LIKE '%混凝土%'
                        OR test_item = 'concrete_table_recognition'
                        OR test_item = 'concrete_strength'
                    )
                    AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
                    ORDER BY test_date DESC, created_at DESC
                """),
                {"pid": project_id}
            )
            
            records = []
            for row in result:
                record = dict(row._mapping)
                # 解析JSONB字段
                if isinstance(record.get("confirmed_result"), str):
                    import json
                    try:
                        record["confirmed_result"] = json.loads(record["confirmed_result"])
                    except Exception:
                        pass
                if isinstance(record.get("raw_result"), str):
                    import json
                    try:
                        record["raw_result"] = json.loads(record["raw_result"])
                    except Exception:
                        pass
                if isinstance(record.get("evidence_refs"), str):
                    import json
                    try:
                        record["evidence_refs"] = json.loads(record["evidence_refs"])
                    except Exception:
                        record["evidence_refs"] = []
                records.append(record)
            
            return records
    
    except Exception as e:
        logger.error(f"获取混凝土数据失败: {e}")
        return []


def _extract_fields(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """???????"""
    table = _build_table(records)
    strength_values = []
    for row in table.get("rows", []):
        val = _parse_number(row[3])
        if val is not None:
            strength_values.append(val)

    if not strength_values:
        for record in records:
            strength = _extract_strength_value(record)
            if strength is not None:
                strength_values.append(strength)

    if not strength_values:
        raise ValueError("?????????")

    avg_strength = round(sum(strength_values) / len(strength_values), 1)
    strength_range = {
        "min": round(min(strength_values), 1),
        "max": round(max(strength_values), 1)
    } if len(strength_values) > 1 else None

    first_record = records[0]

    # ???????
    carbonation_values = []
    for row in table.get("rows", []):
        val = _parse_number(row[4])
        if val is not None:
            carbonation_values.append(val)
    avg_carbonation = round(sum(carbonation_values) / len(carbonation_values), 1) if carbonation_values else _extract_carbonation_depth(first_record)

    # ?????
    all_evidence_refs = []
    record_ids = []
    for record in records:
        refs = record.get("evidence_refs") or []
        if isinstance(refs, list):
            all_evidence_refs.extend(refs)
        record_ids.append(record.get("id"))

    age_days = _extract_age_days_from_record(first_record)
    age_correction_factor = _extract_age_correction_factor_from_record(first_record)
    summary = _build_summary(table)

    return {
        "test_count": len(table.get("rows", [])) if table.get("rows") else len(records),
        "avg_strength": avg_strength,
        "strength_range": strength_range,
        "strength_grade": _extract_strength_grade(first_record),
        "test_method": _extract_test_method(first_record),
        "carbonation_depth": avg_carbonation,
        "test_date": first_record.get("test_date"),
        "evidence_refs": _deduplicate_refs(all_evidence_refs),
        "record_ids": record_ids,
        "code_reference": _determine_code_reference(_extract_test_method(first_record)),
        "age_days": age_days,
        "age_correction_factor": age_correction_factor,
        "table": table,
        "summary": summary
    }


def _extract_strength_value(record: Dict[str, Any]) -> Optional[float]:
    """????? - ????"""
    confirmed = record.get("confirmed_result", {}) or {}

    if isinstance(confirmed, dict):
        strength = confirmed.get("rebound_strength") or confirmed.get("strength_estimated")
        if strength is not None:
            try:
                return float(strength)
            except (ValueError, TypeError):
                pass

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        for key in ["混凝土强度推定值(MPa)", "混凝土强度推定值（MPa）", "混凝土强度推定值", "strength_estimated", "strength_estimated_mpa"]:
            if key in raw and raw.get(key) is not None:
                try:
                    return float(raw.get(key))
                except (ValueError, TypeError):
                    pass

    strength = record.get("strength_estimated_mpa")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass

    strength = record.get("test_result")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass

    return None


def _extract_strength_grade(record: Dict[str, Any]) -> Optional[str]:
    """??????"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        grade = confirmed.get("strength_grade") or confirmed.get("design_strength_grade")
        if grade:
            return str(grade)

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        grade = raw.get("design_strength_grade") or raw.get("??????")
        if grade:
            return str(grade)

    grade = record.get("design_strength_grade")
    return str(grade) if grade else None


def _extract_test_method(record: Dict[str, Any]) -> str:
    """??????"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        method = confirmed.get("test_method")
        if method:
            return str(method)

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        method = raw.get("test_method") or raw.get("检测方法")
        if method:
            return str(method)

    test_item = record.get("test_item") or ""
    if "回弹" in str(test_item):
        return "回弹法"
    return "回弹法"


def _extract_carbonation_depth(record: Dict[str, Any]) -> Optional[float]:
    """??????"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        depth = confirmed.get("carbonation_depth_avg")
        if depth is not None:
            try:
                return float(depth)
            except (ValueError, TypeError):
                pass

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        for key in ["碳化深度(mm)", "碳化深度（mm）", "carbonation_depth_avg"]:
            if key in raw and raw.get(key) is not None:
                try:
                    return float(raw.get(key))
                except (ValueError, TypeError):
                    pass

    depth = record.get("carbonation_depth_avg_mm")
    if depth is not None:
        try:
            return float(depth)
        except (ValueError, TypeError):
            pass

    return None


def _determine_code_reference(test_method: str) -> List[str]:
    """根据检测方法确定规范依据"""
    code_map = {
        "回弹法": ["JGJ/T 23-2011", "GB 50010-2010"],
        "钻芯法": ["CECS 03:2007", "GB 50010-2010"],
        "超声回弹综合法": ["CECS 02:2005", "GB 50010-2010"]
    }
    return code_map.get(test_method, ["JGJ/T 23-2011", "GB 50010-2010"])


def _validate_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """验证数据"""
    warnings = []
    
    # 检查强度值范围
    avg_strength = data.get("avg_strength", 0)
    if not (5.0 <= avg_strength <= 100.0):
        warnings.append(f"混凝土强度值 {avg_strength}MPa 超出常规范围 (5-100)")
    
    # 检查强度等级一致性
    strength_grade = data.get("strength_grade")
    if strength_grade:
        import re
        match = re.match(r"^C(\d+)$", strength_grade)
        if match:
            expected = int(match.group(1))
            deviation = abs(avg_strength - expected) / expected
            if deviation > 0.3:
                warnings.append(f"强度推定值 {avg_strength}MPa 与设计等级 {strength_grade} 差异超过30%")
    
    # 检查碳化深度
    carbonation = data.get("carbonation_depth")
    if carbonation and not (0.0 <= carbonation <= 50.0):
        warnings.append(f"碳化深度 {carbonation}mm 超出常规范围 (0-50)")
    
    return {"warnings": warnings}


def _generate_content_text(data: Dict[str, Any], context: Dict[str, Any]) -> str:
    """生成混凝土强度检测的段落文本（合并旧系统描述逻辑）"""
    code_reference = context.get("code_reference") or "GB50292-2015 附录K"
    test_method = data.get("test_method") or "回弹法"
    test_count = data.get("test_count", 0)
    age_days = _extract_age_days(data)
    carbonation_avg = data.get("carbonation_depth")
    age_correction_factor = _extract_age_correction_factor(data)
    min_strength = data.get("summary", {}).get("min_strength")
    design_grade = data.get("strength_grade") or ""
    meets_design = data.get("summary", {}).get("meets_design")
    
    # 段落1：概述
    paragraphs = []
    paragraphs.append(
        f"本次检测采用{test_method}对混凝土抗压强度进行检测，共检测{test_count}处构件。"
    )
    
    # 段落2：龄期与碳化深度
    age_text = ""
    if age_days is not None:
        if age_days >= 1000:
            age_text = f"混凝土龄期为{age_days}天，已超过1000天，"
            if age_correction_factor:
                age_text += f"依据{code_reference}进行了龄期修正（修正系数{age_correction_factor}）。"
            else:
                age_text += f"依据{code_reference}进行了龄期修正。"
        else:
            age_text = f"混凝土龄期为{age_days}天。"
    
    carbonation_text = ""
    if carbonation_avg is not None:
        if carbonation_avg >= 6.0:
            carbonation_text = f"碳化深度平均值为{carbonation_avg}mm，已超过6mm，依据{code_reference}进行了碳化深度修正。"
        else:
            carbonation_text = f"碳化深度平均值为{carbonation_avg}mm。"
    
    if age_text or carbonation_text:
        paragraphs.append(age_text + carbonation_text)
    
    # 段落3：结果总结
    if min_strength is not None:
        result_text = f"检测结果显示，混凝土抗压强度推定值最小值为{min_strength}MPa"
        if design_grade:
            result_text += f"，设计强度等级为{design_grade}"
        if meets_design is not None:
            result_text += f"，{'符合' if meets_design else '不符合'}设计要求。"
        else:
            result_text += "。"
        paragraphs.append(result_text)
    
    # 段落4：表格引用
    paragraphs.append(f"详见表《构件的混凝土抗压强度及碳化深度抽测结果（{test_method}）》。")
    
    return "\n\n".join(paragraphs)


def _build_table(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """?????????"""
    columns = [
        "序号",
        "抽测部位",
        "抗压强度设计值",
        "龄期修正后混凝土抗压强度推定值(MPa)",
        "碳化深度平均值(mm)",
        "抽测结果评价"
    ]
    raw_rows = []

    for record in records:
        confirmed = record.get("confirmed_result", {}) or {}
        extracted_rows = _extract_raw_rows(record)
        if extracted_rows:
            for raw in extracted_rows:
                location = _get_value(raw, ["检测部位", "test_location", "抽测部位"]) or _extract_location(record, confirmed)
                design_grade = _get_value(raw, ["设计强度等级", "design_strength_grade"]) or _extract_design_grade(record, confirmed)
                strength_estimated = _get_value(raw, ["混凝土强度推定值(MPa)", "混凝土强度推定值（MPa）", "混凝土强度推定值", "strength_estimated", "strength_estimated_mpa"])
                carbonation_avg = _get_value(raw, ["碳化深度(mm)", "碳化深度（mm）", "carbonation_depth_avg"])                     or _extract_carbonation_avg(record, confirmed)

                evaluation = _evaluate_strength(_parse_number(strength_estimated), design_grade)

                raw_rows.append([
                    location,
                    design_grade,
                    _format_number(_parse_number(strength_estimated)),
                    _format_number(_parse_number(carbonation_avg)),
                    evaluation
                ])
        else:
            location = _extract_location(record, confirmed)
            design_grade = _extract_design_grade(record, confirmed)
            strength_estimated = _extract_strength_estimated(record, confirmed)
            carbonation_avg = _extract_carbonation_avg(record, confirmed)
            evaluation = _evaluate_strength(strength_estimated, design_grade)

            raw_rows.append([
                location,
                design_grade,
                _format_number(strength_estimated),
                _format_number(carbonation_avg),
                evaluation
            ])

    rows = []
    for idx, row in enumerate(raw_rows, start=1):
        rows.append([idx] + row)

    return {"columns": columns, "rows": rows}


def _extract_raw_rows(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        rows = raw.get("rows")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
        # ???????raw_result??????
        return [raw]
    return []


def _get_value(data: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in data and data.get(key) is not None:
            return data.get(key)
    return None


def _build_summary(table: Dict[str, Any]) -> Dict[str, Any]:
    """????????????????"""
    strengths = []
    meets_design_flags = []

    for row in table.get("rows", []):
        strength_val = _parse_number(row[3])
        if strength_val is not None:
            strengths.append(strength_val)
        evaluation = row[5]
        if evaluation in ("符合设计要求", "不符合设计要求"):
            meets_design_flags.append(evaluation == "符合设计要求")

    return {
        "min_strength": min(strengths) if strengths else None,
        "meets_design": all(meets_design_flags) if meets_design_flags else None
    }


def _extract_location(record: Dict[str, Any], confirmed: Dict[str, Any]) -> str:
    """???????????????????????"""
    location = confirmed.get("location", {}) if isinstance(confirmed.get("location"), dict) else {}
    description = location.get("description")
    if description:
        return str(description)

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        raw_location = raw.get("检测部位") or raw.get("test_location") or raw.get("抽测部位")
        if raw_location:
            return str(raw_location)

    raw_result = confirmed.get("raw_result", {}) if isinstance(confirmed.get("raw_result"), dict) else {}
    raw_location = raw_result.get("test_location")
    if raw_location:
        return str(raw_location)

    if record.get("test_location_text"):
        return str(record.get("test_location_text"))
    return ""


def _extract_design_grade(record: Dict[str, Any], confirmed: Dict[str, Any]) -> str:
    """???????C30 ??"""
    grade = confirmed.get("design_strength_grade")
    if grade:
        return str(grade)

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        raw_grade = raw.get("设计强度等级") or raw.get("design_strength_grade")
        if raw_grade:
            return str(raw_grade)

    raw_result = confirmed.get("raw_result", {}) if isinstance(confirmed.get("raw_result"), dict) else {}
    raw_grade = raw_result.get("design_strength_grade")
    if raw_grade:
        return str(raw_grade)

    grade = record.get("design_strength_grade")
    return str(grade) if grade else ""


def _extract_strength_estimated(record: Dict[str, Any], confirmed: Dict[str, Any]) -> Optional[float]:
    """???????????????"""
    value = confirmed.get("strength_estimated")
    if value is not None:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return _extract_strength_value(record)


def _extract_carbonation_avg(record: Dict[str, Any], confirmed: Dict[str, Any]) -> Optional[float]:
    """???????"""
    value = confirmed.get("carbonation_depth_avg")
    if value is not None:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return _extract_carbonation_depth(record)


def _evaluate_strength(strength_estimated: Optional[float], design_grade: str) -> str:
    """??????????????"""
    design_value = _parse_design_grade(design_grade)
    if strength_estimated is None or design_value is None:
        return ""
    return "符合设计要求" if strength_estimated >= design_value else "不符合设计要求"


def _parse_design_grade(grade: str) -> Optional[float]:
    """? C30 ??? 30"""
    if not grade:
        return None
    import re
    match = re.match(r"^C(\d+)$", str(grade))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _format_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    try:
        return str(round(float(value), 1))
    except (ValueError, TypeError):
        return ""


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_date_string(value: Any):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _extract_age_days_from_record(record: Dict[str, Any]) -> Optional[int]:
    """?????? raw_result/confirmed_result ?????"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        raw_result = confirmed.get("raw_result", {}) if isinstance(confirmed.get("raw_result"), dict) else {}
        age_days = raw_result.get("concrete_age_days") or confirmed.get("concrete_age_days")
        if age_days is not None:
            try:
                return int(age_days)
            except (ValueError, TypeError):
                return None

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        age_days = raw.get("concrete_age_days")
        if age_days is not None:
            try:
                return int(age_days)
            except (ValueError, TypeError):
                return None

        build_date = raw.get("施工日期")
        test_date = raw.get("检测日期") or raw.get("test_date")
        if build_date and test_date:
            build_dt = _parse_date_string(build_date)
            test_dt = _parse_date_string(test_date)
            if build_dt and test_dt:
                delta = test_dt - build_dt
                return delta.days

    return None


def _extract_age_correction_factor_from_record(record: Dict[str, Any]) -> Optional[float]:
    """?????????? confirmed_result/raw_result ??"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        factor = confirmed.get("age_correction_factor")
        if factor is not None:
            try:
                return float(factor)
            except (ValueError, TypeError):
                return None

    raw = record.get("raw_result", {}) or {}
    if isinstance(raw, dict):
        factor = raw.get("age_correction_factor") or raw.get("修正系数")
        if factor is not None:
            try:
                return float(factor)
            except (ValueError, TypeError):
                return None

    return None


def _extract_age_days(data: Dict[str, Any]) -> Optional[int]:
    """??????????????????"""
    raw = data.get("age_days")
    if raw is None:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def _extract_age_correction_factor(data: Dict[str, Any]) -> Optional[float]:
    """??????????????????????"""
    raw = data.get("age_correction_factor")
    if raw is None:
        return None
    try:
        return float(raw)
    except (ValueError, TypeError):
        return None
def _deduplicate_refs(refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复的证据引用"""
    seen = set()
    unique = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        key = ref.get("object_key") or ref.get("id")
        if key and key not in seen:
            unique.append(ref)
            seen.add(key)
    return unique
