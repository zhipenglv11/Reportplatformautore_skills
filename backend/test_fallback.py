# -*- coding: utf-8 -*-
"""
测试容错逻辑：使用错误的 source_node_id 应该能自动回退查询
"""

import asyncio

async def test_fallback_logic():
    """测试容错逻辑"""
    from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
    from skills_library.generation.inspection.material_strength.subskills.mortar_strength.impl.parse import parse_mortar_strength
    
    print("="  * 80)
    print("测试容错逻辑：使用错误的 source_node_id")
    print("=" * 80)
    
    # 测试砖强度
    print("\n1. 砖强度 - 错误的 source_node_id:")
    context = {"source_node_id": "wrong-node-id-12345"}
    result = await parse_brick_strength("1", "test-node", context)
    print(f"   record_count: {result.get('meta', {}).get('record_count')}")
    print(f"   has_data: {result.get('meta', {}).get('has_data')}")
    print(f"   warnings: {result.get('meta', {}).get('warnings')}")
    
    # 测试砂浆强度
    print("\n2. 砂浆强度 - 错误的 source_node_id:")
    context = {"source_node_id": "another-wrong-id"}
    result = await parse_mortar_strength("1", "test-node", context)
    print(f"   record_count: {result.get('meta', {}).get('record_count')}")
    print(f"   has_data: {result.get('meta', {}).get('has_data')}")
    print(f"   warnings: {result.get('meta', {}).get('warnings')}")
    
    print("\n" + "=" * 80)
    print("测试完成！如果 record_count > 0，说明容错逻辑生效了。")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_fallback_logic())
