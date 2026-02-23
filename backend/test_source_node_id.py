# -*- coding: utf-8 -*-
"""
测试带 source_node_id 参数的情况
"""

import asyncio

async def test_with_source_node_id():
    """测试带 source_node_id 的情况"""
    from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
    
    print("=" * 80)
    print("测试砖强度 API（带 source_node_id）")
    print("=" * 80)
    
    # 使用数据库中实际的 node_id
    test_cases = [
        {"project_id": "1", "source_node_id": "collection-1769823801623", "desc": "砖 node_id 1"},
        {"project_id": "1", "source_node_id": "collection-1769823550775", "desc": "砖 node_id 2"},
        {"project_id": "1", "source_node_id": "collection-1769242176129", "desc": "砖 node_id 3"},
        {"project_id": "1", "source_node_id": "wrong-node-id", "desc": "错误的 node_id"},
        {"project_id": "1", "source_node_id": "scope_brick_strength", "desc": "scope 过滤"},
    ]
    
    for test_case in test_cases:
        project_id = test_case["project_id"]
        source_node_id = test_case["source_node_id"]
        desc = test_case["desc"]
        
        context = {"source_node_id": source_node_id}
        
        print(f"\n{desc}:")
        print(f"  source_node_id: {source_node_id}")
        
        result = await parse_brick_strength(project_id, "test-node", context)
        
        print(f"  -> Found records: {result.get('meta', {}).get('record_count')}")
        if result.get('meta', {}).get('warnings'):
            print(f"  -> Warnings: {result.get('meta', {}).get('warnings')}")


if __name__ == "__main__":
    asyncio.run(test_with_source_node_id())
