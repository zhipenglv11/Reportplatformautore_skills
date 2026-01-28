"""
Material Strength - 父Skill编排器
负责调用子skills并组装成完整章节
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def assemble_material_strength(
    project_id: str,
    node_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    编排材料强度章节
    
    Args:
        project_id: 项目ID
        node_id: 节点ID
        context: 上下文配置
    
    Returns:
        组装后的完整章节数据
    """
    context = context or {}
    
    # 1. 检测可用的材料类型
    available_materials = await detect_available_materials(project_id, node_id)
    
    if not available_materials:
        logger.info(f"Project {project_id}, Node {node_id}: 未找到任何材料强度数据")
        return {
            "has_data": False,
            "sections": [],
            "assembled_content": "本次检测未对材料强度进行检测。",
            "summary": {"material_types": [], "total_test_count": 0},
            "evidence_refs": [],
            "generation_metadata": {
                "skill_name": "material_strength_description",
                "skill_version": "2.0.0",
                "subskills_called": [],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    # 2. 确定调用顺序
    material_order = context.get("material_order", ["concrete", "brick", "mortar"])
    
    # 3. 调用子skills
    sections = []
    all_evidence_refs = []
    total_test_count = 0
    subskills_called = []
    
    for material_type in material_order:
        if material_type not in available_materials:
            continue
        
        try:
            # 调用对应的子skill
            subskill_result = await call_subskill(
                material_type=material_type,
                project_id=project_id,
                node_id=node_id,
                context=context
            )
            
            if subskill_result.get("has_data"):
                sections.append(subskill_result)
                subskills_called.append(f"{material_type}_strength")
                
                # 收集证据和统计
                all_evidence_refs.extend(subskill_result.get("evidence_refs", []))
                total_test_count += subskill_result.get("test_count", 0)
        
        except Exception as e:
            logger.error(f"调用子skill {material_type}_strength 失败: {e}")
            # 继续执行其他子skills
    
    # 4. 组装段落
    include_overview = context.get("include_overview", False)
    assembled_content = assemble_content(sections, include_overview)
    
    # 5. 生成汇总
    summary = {
        "material_types": [s.get("material_type") for s in sections],
        "total_test_count": total_test_count
    }
    
    return {
        "has_data": len(sections) > 0,
        "sections": sections,
        "assembled_content": assembled_content,
        "summary": summary,
        "evidence_refs": _deduplicate_evidence_refs(all_evidence_refs),
        "generation_metadata": {
            "skill_name": "material_strength_description",
            "skill_version": "2.0.0",
            "subskills_called": subskills_called,
            "generated_at": datetime.utcnow().isoformat(),
            "section_count": len(sections)
        }
    }


async def detect_available_materials(
    project_id: str,
    node_id: str
) -> List[str]:
    """
    检测哪些材料类型有有效数据
    
    Returns:
        可用的材料类型列表，如 ["concrete", "brick", "mortar"]
    """
    # 这里需要查询 professional_data 表
    # 检查哪些 dataset_key 存在有效数据
    
    # TODO: 实现数据库查询
    # 示例查询逻辑：
    # SELECT DISTINCT test_item FROM professional_data
    # WHERE project_id = ? AND node_id = ?
    # AND confirmed_result IS NOT NULL
    
    # 临时实现（需要连接实际数据库）
    from models.db import get_engine
    
    available = []
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # 检查混凝土数据
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM professional_data
                    WHERE project_id = :pid AND node_id = :nid
                    AND test_item LIKE '%混凝土%'
                    AND confirmed_result IS NOT NULL
                """),
                {"pid": project_id, "nid": node_id}
            )
            if result.scalar() > 0:
                available.append("concrete")
            
            # 检查砌体砖数据
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM professional_data
                    WHERE project_id = :pid AND node_id = :nid
                    AND (test_item LIKE '%砌体砖%' OR test_item LIKE '%砖强度%')
                    AND confirmed_result IS NOT NULL
                """),
                {"pid": project_id, "nid": node_id}
            )
            if result.scalar() > 0:
                available.append("brick")
            
            # 检查砂浆数据
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as cnt FROM professional_data
                    WHERE project_id = :pid AND node_id = :nid
                    AND test_item LIKE '%砂浆%'
                    AND confirmed_result IS NOT NULL
                """),
                {"pid": project_id, "nid": node_id}
            )
            if result.scalar() > 0:
                available.append("mortar")
    
    except Exception as e:
        logger.error(f"检测材料数据可用性失败: {e}")
    
    return available


async def call_subskill(
    material_type: str,
    project_id: str,
    node_id: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    调用指定的子skill
    
    Args:
        material_type: 材料类型 (concrete, brick, mortar)
        project_id: 项目ID
        node_id: 节点ID
        context: 上下文
    
    Returns:
        子skill的执行结果
    """
    # 导入对应的子skill
    if material_type == "concrete":
        from ..subskills.concrete_strength.impl.parse import parse_concrete_strength
        return await parse_concrete_strength(project_id, node_id, context)
    
    elif material_type == "brick":
        from ..subskills.brick_strength.impl.parse import parse_brick_strength
        return await parse_brick_strength(project_id, node_id, context)
    
    elif material_type == "mortar":
        from ..subskills.mortar_strength.impl.parse import parse_mortar_strength
        return await parse_mortar_strength(project_id, node_id, context)
    
    else:
        logger.warning(f"未知的材料类型: {material_type}")
        return {"has_data": False}


def assemble_content(
    sections: List[Dict[str, Any]],
    include_overview: bool = False
) -> str:
    """
    组装各子skill的内容成完整章节
    
    Args:
        sections: 各子skill的输出列表
        include_overview: 是否包含总述
    
    Returns:
        组装后的文本内容
    """
    if not sections:
        return "本次检测未对材料强度进行检测。"
    
    paragraphs = []
    
    # 可选：添加总述
    if include_overview:
        overview = generate_overview(sections)
        if overview:
            paragraphs.append(overview)
    
    # 添加各子section的内容
    for section in sections:
        content = section.get("content", "")
        if content:
            paragraphs.append(content)
    
    # 用双换行符连接段落
    return "\n\n".join(paragraphs)


def generate_overview(sections: List[Dict[str, Any]]) -> Optional[str]:
    """
    生成总述段落（可选功能）
    
    例如："本次检测对混凝土、砌体砖等材料强度进行了检测，共计8个检测点。"
    """
    if not sections:
        return None
    
    material_names = {
        "concrete": "混凝土",
        "brick": "砌体砖",
        "mortar": "砂浆"
    }
    
    materials = [material_names.get(s.get("material_type"), "") for s in sections if s.get("material_type")]
    material_list = "、".join(materials)
    
    total_count = sum(s.get("test_count", 0) for s in sections)
    
    return f"本次检测对{material_list}等材料强度进行了检测，共计{total_count}个检测点。"


def _deduplicate_evidence_refs(refs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复的证据引用"""
    seen_keys = set()
    unique_refs = []
    
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        
        key = ref.get("object_key") or ref.get("id")
        if key and key not in seen_keys:
            unique_refs.append(ref)
            seen_keys.add(key)
    
    return unique_refs
