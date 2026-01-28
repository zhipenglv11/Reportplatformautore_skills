"""
Brick Strength Sub-Skill - 数据解析与生成
专门负责砌体砖强度检测描述
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def parse_brick_strength(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    解析砌体砖强度数据并生成描述
    
    Args:
        project_id: 项目ID
        node_id: 节点ID
        context: 上下文配置
    
    Returns:
        结构化的砌体砖强度描述数据
    """
    # 1. 从数据库读取砌体砖数据
    records = await _fetch_brick_data(project_id, node_id)
    
    if not records:
        logger.info(f"Project {project_id}, Node {node_id}: 未找到砌体砖强度数据")
        return {
            "has_data": False,
            "material_type": "brick"
        }
    
    # 2. 提取字段数据
    parsed_data = _extract_fields(records)
    
    # 3. 验证数据
    validation = _validate_data(parsed_data)
    if validation["warnings"]:
        logger.warning(f"砌体砖数据验证警告: {validation['warnings']}")
    
    # 4. 生成描述文字
    content = _generate_content(parsed_data)
    
    # 5. 返回结构化结果
    return {
        "has_data": True,
        "material_type": "brick",
        "title": "砌体砖强度",
        "content": content,
        "test_count": parsed_data["test_count"],
        "test_method": parsed_data["test_method"],
        "avg_strength": parsed_data["avg_strength"],
        "strength_range": parsed_data.get("strength_range"),
        "strength_grade": parsed_data.get("strength_grade"),
        "strength_unit": "MPa",
        "evidence_refs": parsed_data["evidence_refs"],
        "record_ids": parsed_data["record_ids"],
        "generation_metadata": {
            "skill_name": "brick_strength",
            "skill_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "record_count": len(records),
            "test_methods_used": [parsed_data["test_method"]],
            "warnings": validation["warnings"]
        }
    }


async def _fetch_brick_data(project_id: str, node_id: str) -> List[Dict[str, Any]]:
    """从professional_data表获取砌体砖数据"""
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
                        test_date,
                        test_location_text,
                        confirmed_result,
                        evidence_refs
                    FROM professional_data
                    WHERE project_id = :pid
                    AND node_id = :nid
                    AND (test_item LIKE '%砌体砖%' OR test_item LIKE '%砖强度%')
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
        logger.error(f"获取砌体砖数据失败: {e}")
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
        "test_date": first_record.get("test_date"),
        "evidence_refs": _deduplicate_refs(all_evidence_refs),
        "record_ids": record_ids,
        "code_reference": ["GB/T 50315-2011", "GB 50003-2011"]
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
    """提取强度等级（砌体砖用MU格式）"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        grade = confirmed.get("strength_grade")
        if grade:
            grade_str = str(grade)
            # 验证MU格式
            import re
            if re.match(r"^MU\d+$", grade_str):
                return grade_str
    
    grade = record.get("design_strength_grade")
    if grade:
        grade_str = str(grade)
        import re
        if re.match(r"^MU\d+$", grade_str):
            return grade_str
    
    return None


def _extract_test_method(record: Dict[str, Any]) -> str:
    """提取检测方法"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        method = confirmed.get("test_method")
        if method:
            return str(method)
    return "回弹法"


def _deduplicate_refs(refs: List[Dict]) -> List[Dict]:
    """去重证据引用"""
    seen = set()
    unique = []
    for ref in refs:
        key = (ref.get("record_id"), ref.get("field_path"))
        if key not in seen:
            seen.add(key)
            unique.append(ref)
    return unique


def _validate_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """验证数据质量"""
    warnings = []
    
    # 检查test_count
    if data["test_count"] < 1:
        warnings.append("检测部位数量少于1")
    
    # 检查强度范围
    if data["avg_strength"] < 3.0 or data["avg_strength"] > 50.0:
        warnings.append(f"平均强度{data['avg_strength']}MPa超出常见范围(3~50MPa)")
    
    # 检查强度等级匹配
    if data.get("strength_grade"):
        import re
        match = re.match(r"^MU(\d+)$", data["strength_grade"])
        if match:
            grade_num = int(match.group(1))
            if data["avg_strength"] < grade_num * 0.7:
                warnings.append(f"平均强度{data['avg_strength']}MPa低于等级{data['strength_grade']}的70%")
    
    return {"valid": len(warnings) == 0, "warnings": warnings}


def _generate_content(data: Dict[str, Any]) -> str:
    """生成描述文字"""
    parts = []
    
    # 第1部分：检测概述
    overview = f"砌体砖采用{data['test_method']}检测，检测{data['test_count']}个部位"
    parts.append(overview + "。")
    
    # 第2部分：检测结果
    result_parts = []
    
    if data.get("strength_grade"):
        result_parts.append(f"强度等级推定为{data['strength_grade']}")
    
    result_parts.append(f"强度推定值为{data['avg_strength']}MPa")
    
    if data.get("strength_range") and data["test_count"] > 1:
        range_str = f"在{data['strength_range']['min']}~{data['strength_range']['max']}MPa之间"
        result_parts.insert(0, f"砖强度推定值{range_str}")
        result_parts[1] = f"平均值为{data['avg_strength']}MPa"
    
    parts.append("，".join(result_parts) + "。")
    
    # 第3部分：规范依据
    code_list = "、".join(data["code_reference"])
    parts.append(f"相关检测及结果判定依据{code_list}执行。")
    
    return "".join(parts)
