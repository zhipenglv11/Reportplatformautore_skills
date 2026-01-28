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
            "has_data": False,
            "material_type": "concrete"
        }
    
    # 2. 提取字段数据
    parsed_data = _extract_fields(records)
    
    # 3. 验证数据
    validation = _validate_data(parsed_data)
    if validation["warnings"]:
        logger.warning(f"混凝土数据验证警告: {validation['warnings']}")
    
    # 4. 生成描述文字
    content = _generate_content(parsed_data)
    
    # 5. 返回结构化结果
    return {
        "has_data": True,
        "material_type": "concrete",
        "title": "混凝土强度",
        "content": content,
        "test_count": parsed_data["test_count"],
        "test_method": parsed_data["test_method"],
        "avg_strength": parsed_data["avg_strength"],
        "strength_range": parsed_data.get("strength_range"),
        "strength_grade": parsed_data.get("strength_grade"),
        "carbonation_depth": parsed_data.get("carbonation_depth"),
        "strength_unit": "MPa",
        "evidence_refs": parsed_data["evidence_refs"],
        "record_ids": parsed_data["record_ids"],
        "generation_metadata": {
            "skill_name": "concrete_strength",
            "skill_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "record_count": len(records),
            "test_methods_used": [parsed_data["test_method"]],
            "warnings": validation["warnings"]
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
                        confirmed_result,
                        evidence_refs
                    FROM professional_data
                    WHERE project_id = :pid
                    AND node_id = :nid
                    AND test_item LIKE '%混凝土%'
                    AND confirmed_result IS NOT NULL
                    ORDER BY test_date DESC, created_at DESC
                """),
                {"pid": project_id, "nid": node_id}
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
    """按fields.yaml定义提取字段"""
    # 提取强度值
    strength_values = []
    for record in records:
        strength = _extract_strength_value(record)
        if strength is not None:
            strength_values.append(strength)
    
    if not strength_values:
        raise ValueError("未找到有效的强度值")
    
    # 计算统计值
    avg_strength = round(sum(strength_values) / len(strength_values), 1)
    strength_range = {
        "min": round(min(strength_values), 1),
        "max": round(max(strength_values), 1)
    } if len(strength_values) > 1 else None
    
    # 提取其他字段（从第一条记录）
    first_record = records[0]
    confirmed = first_record.get("confirmed_result", {}) or {}
    
    # 碳化深度
    carbonation_depths = []
    for record in records:
        depth = _extract_carbonation_depth(record)
        if depth is not None:
            carbonation_depths.append(depth)
    
    avg_carbonation = round(sum(carbonation_depths) / len(carbonation_depths), 1) if carbonation_depths else None
    
    # 收集证据
    all_evidence_refs = []
    record_ids = []
    for record in records:
        refs = record.get("evidence_refs") or []
        if isinstance(refs, list):
            all_evidence_refs.extend(refs)
        record_ids.append(record.get("id"))
    
    return {
        "test_count": len(records),
        "avg_strength": avg_strength,
        "strength_range": strength_range,
        "strength_grade": _extract_strength_grade(first_record),
        "test_method": _extract_test_method(first_record),
        "carbonation_depth": avg_carbonation,
        "test_date": first_record.get("test_date"),
        "evidence_refs": _deduplicate_refs(all_evidence_refs),
        "record_ids": record_ids,
        "code_reference": _determine_code_reference(_extract_test_method(first_record))
    }


def _extract_strength_value(record: Dict[str, Any]) -> Optional[float]:
    """提取强度值 - 按优先级"""
    confirmed = record.get("confirmed_result", {}) or {}
    
    # 优先级1
    if isinstance(confirmed, dict):
        strength = confirmed.get("rebound_strength") or confirmed.get("strength_estimated")
        if strength is not None:
            try:
                return float(strength)
            except (ValueError, TypeError):
                pass
    
    # 优先级2
    strength = record.get("strength_estimated_mpa")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass
    
    # 优先级3
    strength = record.get("test_result")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass
    
    return None


def _extract_strength_grade(record: Dict[str, Any]) -> Optional[str]:
    """提取强度等级"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        grade = confirmed.get("strength_grade")
        if grade:
            return str(grade)
    
    grade = record.get("design_strength_grade")
    return str(grade) if grade else None


def _extract_test_method(record: Dict[str, Any]) -> str:
    """提取检测方法"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        method = confirmed.get("test_method")
        if method:
            return str(method)
    return "回弹法"


def _extract_carbonation_depth(record: Dict[str, Any]) -> Optional[float]:
    """提取碳化深度"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        depth = confirmed.get("carbonation_depth_avg")
        if depth is not None:
            try:
                return float(depth)
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


def _generate_content(data: Dict[str, Any]) -> str:
    """根据render.md规范生成描述文字"""
    paragraphs = []
    
    # 第1段：检测概述
    overview = f"采用{data['test_method']}对现场混凝土强度进行检测，共检测{data['test_count']}个构件。"
    paragraphs.append(overview)
    
    # 第2段：检测结果
    strength_grade = data.get("strength_grade")
    carbonation = data.get("carbonation_depth")
    strength_range = data.get("strength_range")
    
    if strength_grade and carbonation:
        result = f"检测结果表明，混凝土强度推定值在{strength_range['min']}~{strength_range['max']}MPa之间，" \
                 f"平均值为{data['avg_strength']}MPa，设计强度等级为{strength_grade}。" \
                 f"碳化深度平均值为{carbonation}mm。"
    elif strength_grade:
        result = f"检测结果表明，混凝土强度推定值为{data['avg_strength']}MPa，设计强度等级为{strength_grade}。"
    elif strength_range:
        result = f"混凝土强度检测结果显示，各检测构件强度推定值在{strength_range['min']}~{strength_range['max']}MPa之间，" \
                 f"平均值为{data['avg_strength']}MPa。"
    else:
        result = f"混凝土强度检测结果为{data['avg_strength']}MPa。"
    
    paragraphs.append(result)
    
    # 第3段：规范依据
    code_list = "、".join(data["code_reference"])
    code_ref = f"相关检测及结果判定依据{code_list}执行。"
    paragraphs.append(code_ref)
    
    return "".join(paragraphs)


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
