from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RecordSpec:
    business_type: str
    name: str


@dataclass(frozen=True)
class RecordPattern:
    pattern: str
    business_type: str
    name: str
    priority: int = 0


# 1. 精确匹配字典 (Legacy/Override)
# 记录编号 -> 业务类型/中文名称
RECORD_REGISTRY: Dict[str, RecordSpec] = {
    # 示例保留，优先通过 Pattern 匹配
    "KSQR-4.13-XC-10": RecordSpec(business_type="concrete_rebound_record", name="回弹原始记录表"),
}

# 2. 模式匹配列表 (New)
# 按 priority 降序排列 (高优先级在前)
RECORD_CODE_PATTERNS: List[RecordPattern] = [
    # KSQR系列 - 通常为回弹原始记录
    RecordPattern(
        pattern=r"^KSQR-.*",
        business_type="concrete_rebound_record",
        name="回弹原始记录 (KSQR)",
        priority=50
    ),
    # KJQR系列 - 通用/其他原始记录
    RecordPattern(
        pattern=r"^KJQR-.*",
        business_type="generic_raw_record",
        name="通用原始记录 (KJQR)",
        priority=40
    ),
]

# 节点 -> 业务类型（可按 node_id 精确匹配或关键字匹配）
NODE_TYPE_MAP: Dict[str, str] = {
    "node_concrete_rebound_upload": "concrete_rebound_record",
    "node_concrete_strength_upload": "concrete_strength",
}

# dataset_key / template_id -> 业务类型
DATASET_TYPE_MAP: Dict[str, str] = {
    "concrete_strength": "concrete_strength",
    "concrete_rebound_record_sheet": "concrete_rebound_record",
}
TEMPLATE_TYPE_MAP: Dict[str, str] = {
    "concrete_strength_v1": "concrete_strength",
    "rebound_record_v1": "concrete_rebound_record",
}

def resolve_expected_type(
    node_id: str,
    template_id: Optional[str] = None,
    dataset_key: Optional[str] = None,
) -> Optional[str]:
    if template_id and template_id in TEMPLATE_TYPE_MAP:
        return TEMPLATE_TYPE_MAP[template_id]
    if dataset_key and dataset_key in DATASET_TYPE_MAP:
        return DATASET_TYPE_MAP[dataset_key]
    if node_id in NODE_TYPE_MAP:
        return NODE_TYPE_MAP[node_id]
    node_id_lower = node_id.lower()
    for key, value in NODE_TYPE_MAP.items():
        if key.lower() in node_id_lower:
            return value
    return None


def resolve_record_type(record_code: Optional[str]) -> Optional[RecordSpec]:
    """
    解析 record_code 对应的业务类型。
    策略:
    1. 精确匹配 RECORD_REGISTRY
    2. 正则匹配 RECORD_CODE_PATTERNS (按 priority 排序)
    """
    if not record_code:
        return None
        
    # 1. Exact Match
    if record_code in RECORD_REGISTRY:
        return RECORD_REGISTRY[record_code]

    # 2. Pattern Match
    for pattern in sorted(RECORD_CODE_PATTERNS, key=lambda item: item.priority, reverse=True):
        try:
            if re.match(pattern.pattern, record_code):
                return RecordSpec(business_type=pattern.business_type, name=pattern.name)
        except re.error:
            continue
    return None


def resolve_record_name(business_type: Optional[str]) -> Optional[str]:
    if not business_type:
        return None
    # 查找名称逻辑优化：遍历注册表和模式列表（或维护一个单独的名称映射，这里简单处理）
    # 优先从 RECORD_REGISTRY 找
    for spec in RECORD_REGISTRY.values():
        if spec.business_type == business_type:
            return spec.name
    # 其次从 Patterns 找
    for pat in RECORD_CODE_PATTERNS:
        if pat.business_type == business_type:
            return pat.name
    # Fallback
    return business_type
