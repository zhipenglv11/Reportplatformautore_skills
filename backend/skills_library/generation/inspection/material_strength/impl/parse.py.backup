"""
Material Strength Skill - 数据解析模块
从 professional_data 表读取材料强度数据并转换为 fields.yaml 定义的结构
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_material_strength(
    records: List[Dict[str, Any]],
    project_id: str,
    node_id: str
) -> Dict[str, Any]:
    """
    解析材料强度检测数据
    
    Args:
        records: professional_data 表的查询结果列表
        project_id: 项目ID
        node_id: 节点ID
    
    Returns:
        符合 fields.yaml 定义的结构化数据字典
    """
    if not records:
        logger.warning(f"Project {project_id}, Node {node_id}: 未找到材料强度检测数据")
        return {
            "has_data": False,
            "test_count": 0,
            "message": "未进行材料强度检测"
        }
    
    # 按材料类型分组
    grouped_data = _group_by_material_type(records)
    
    # 解析各材料类型的数据
    parsed_materials = []
    all_evidence_refs = []
    all_record_ids = []
    
    for material_type, material_records in grouped_data.items():
        material_data = _parse_material_group(material_type, material_records)
        if material_data:
            parsed_materials.append(material_data)
            all_evidence_refs.extend(material_data.get("evidence_refs", []))
            all_record_ids.extend(material_data.get("record_ids", []))
    
    # 汇总统计
    summary = _calculate_summary(parsed_materials)
    
    return {
        "has_data": True,
        "materials": parsed_materials,
        "summary": summary,
        "evidence": {
            "evidence_refs": all_evidence_refs,
            "record_ids": all_record_ids
        },
        "metadata": {
            "total_records": len(records),
            "material_types": list(grouped_data.keys()),
            "parsed_at": datetime.utcnow().isoformat()
        }
    }


def _group_by_material_type(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按材料类型分组"""
    grouped = {}
    
    for record in records:
        # 优先级1: 从 confirmed_result 获取
        material_type = None
        confirmed = record.get("confirmed_result")
        if confirmed and isinstance(confirmed, dict):
            material_type = confirmed.get("material_type")
        
        # 优先级2: 从 test_item 推断
        if not material_type:
            test_item = record.get("test_item", "")
            if "混凝土" in test_item:
                material_type = "混凝土"
            elif "砌体砖" in test_item or "砖" in test_item:
                material_type = "砌体砖"
            elif "砌块" in test_item:
                material_type = "砌块"
            elif "砂浆" in test_item:
                material_type = "砂浆"
        
        # 默认分类
        if not material_type:
            material_type = "未知材料"
        
        if material_type not in grouped:
            grouped[material_type] = []
        grouped[material_type].append(record)
    
    return grouped


def _parse_material_group(material_type: str, records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """解析单一材料类型的数据"""
    if not records:
        return None
    
    # 提取强度值列表
    strength_values = []
    for record in records:
        strength = _extract_strength_value(record)
        if strength is not None:
            strength_values.append(strength)
    
    if not strength_values:
        logger.warning(f"材料类型 {material_type} 未找到有效强度值")
        return None
    
    # 计算平均值和范围
    avg_strength = round(sum(strength_values) / len(strength_values), 1)
    strength_range = {
        "min": round(min(strength_values), 1),
        "max": round(max(strength_values), 1)
    }
    
    # 提取其他字段
    first_record = records[0]
    confirmed = first_record.get("confirmed_result", {}) or {}
    
    result = {
        "material_type": material_type,
        "test_count": len(records),
        "strength_value": avg_strength,
        "strength_range": strength_range if len(strength_values) > 1 else None,
        "test_method": _extract_test_method(first_record),
        "strength_grade": _extract_strength_grade(first_record),
        "test_date": _extract_test_date(first_record),
        "test_locations": _extract_test_locations(records),
        "code_reference": _determine_code_reference(material_type),
        "evidence_refs": _collect_evidence_refs(records),
        "record_ids": [r.get("id") for r in records if r.get("id")]
    }
    
    # 混凝土特有：碳化深度
    if material_type == "混凝土":
        carbonation_depths = []
        for record in records:
            depth = _extract_carbonation_depth(record)
            if depth is not None:
                carbonation_depths.append(depth)
        if carbonation_depths:
            result["carbonation_depth"] = round(sum(carbonation_depths) / len(carbonation_depths), 1)
    
    return result


def _extract_strength_value(record: Dict[str, Any]) -> Optional[float]:
    """提取强度值 - 按优先级"""
    # 优先级1: confirmed_result.rebound_strength
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        strength = confirmed.get("rebound_strength") or confirmed.get("strength_estimated")
        if strength is not None:
            try:
                return float(strength)
            except (ValueError, TypeError):
                pass
    
    # 优先级2: strength_estimated_mpa
    strength = record.get("strength_estimated_mpa")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass
    
    # 优先级3: test_result
    strength = record.get("test_result")
    if strength is not None:
        try:
            return float(strength)
        except (ValueError, TypeError):
            pass
    
    return None


def _extract_test_method(record: Dict[str, Any]) -> str:
    """提取检测方法"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        method = confirmed.get("test_method")
        if method:
            return str(method)
    
    # 默认为回弹法
    return "回弹法"


def _extract_strength_grade(record: Dict[str, Any]) -> Optional[str]:
    """提取强度等级"""
    confirmed = record.get("confirmed_result", {}) or {}
    if isinstance(confirmed, dict):
        grade = confirmed.get("strength_grade")
        if grade:
            return str(grade)
    
    grade = record.get("design_strength_grade")
    if grade:
        return str(grade)
    
    return None


def _extract_test_date(record: Dict[str, Any]) -> Optional[str]:
    """提取检测日期"""
    test_date = record.get("test_date")
    if test_date:
        # 确保日期格式
        if isinstance(test_date, str):
            return test_date
        try:
            return test_date.strftime("%Y-%m-%d")
        except AttributeError:
            pass
    return None


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


def _extract_test_locations(records: List[Dict[str, Any]]) -> List[str]:
    """提取检测部位列表"""
    locations = []
    for record in records:
        location = record.get("test_location_text")
        if location:
            locations.append(str(location))
    return locations


def _collect_evidence_refs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """收集证据引用"""
    all_refs = []
    for record in records:
        refs = record.get("evidence_refs")
        if refs:
            if isinstance(refs, list):
                all_refs.extend(refs)
            elif isinstance(refs, str):
                # 如果是JSON字符串，尝试解析
                try:
                    import json
                    parsed_refs = json.loads(refs)
                    if isinstance(parsed_refs, list):
                        all_refs.extend(parsed_refs)
                except Exception:
                    pass
    
    # 去重（基于ref的某个唯一标识，如object_key）
    unique_refs = []
    seen_keys = set()
    for ref in all_refs:
        if isinstance(ref, dict):
            key = ref.get("object_key") or ref.get("id")
            if key and key not in seen_keys:
                unique_refs.append(ref)
                seen_keys.add(key)
    
    return unique_refs


def _determine_code_reference(material_type: str) -> List[str]:
    """根据材料类型确定规范依据"""
    code_map = {
        "混凝土": ["JGJ/T 23-2011", "GB 50010-2010"],
        "砌体砖": ["GB/T 50315-2011", "GB 50003-2011"],
        "砌块": ["GB/T 50315-2011", "GB 50003-2011"],
        "砂浆": ["JGJ/T 70-2009"]
    }
    return code_map.get(material_type, ["相关国家规范"])


def _calculate_summary(materials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算汇总统计"""
    total_count = sum(m.get("test_count", 0) for m in materials)
    
    # 收集所有强度值计算总平均
    all_strengths = []
    for material in materials:
        count = material.get("test_count", 0)
        avg = material.get("strength_value", 0)
        # 按数量加权
        all_strengths.extend([avg] * count)
    
    avg_strength = round(sum(all_strengths) / len(all_strengths), 1) if all_strengths else 0
    
    material_types = [m.get("material_type") for m in materials if m.get("material_type")]
    
    return {
        "total_count": total_count,
        "material_types": material_types,
        "avg_strength": avg_strength,
        "strength_unit": "MPa",
        "material_count": len(materials)
    }


# ==================== 可选：验证函数 ====================

def validate_parsed_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证解析后的数据是否符合 fields.yaml 的约束
    
    Returns:
        {"valid": bool, "errors": List[str], "warnings": List[str]}
    """
    errors = []
    warnings = []
    
    if not data.get("has_data"):
        return {"valid": True, "errors": [], "warnings": ["无检测数据"]}
    
    materials = data.get("materials", [])
    
    for material in materials:
        material_type = material.get("material_type")
        
        # 检查必填字段
        if not material_type:
            errors.append("材料类型不能为空")
        
        strength = material.get("strength_value")
        if strength is None:
            errors.append(f"{material_type}: 强度值不能为空")
        elif not (0 <= strength <= 100):
            warnings.append(f"{material_type}: 强度值 {strength}MPa 超出常规范围 (0-100)")
        
        # 检查强度等级格式
        grade = material.get("strength_grade")
        if grade:
            import re
            if not re.match(r"^(C\d+|MU\d+|M\d+\.\d+)$", grade):
                warnings.append(f"{material_type}: 强度等级格式不正确 '{grade}'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
