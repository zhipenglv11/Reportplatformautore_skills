# -*- coding: utf-8 -*-
"""
测试砖和砂浆强度 API 调用
"""

import asyncio
import json
import sys

async def test_brick_strength():
    """测试砖强度 API"""
    from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
    
    print("=" * 80)
    print("测试砖强度 API")
    print("=" * 80)
    
    # 使用数据库中实际的 project_id
    project_id = "1"
    node_id = "chapter-brick-strength"
    context = {}
    
    print(f"\n调用参数:")
    print(f"  project_id: {project_id}")
    print(f"  node_id: {node_id}")
    print(f"  context: {context}")
    
    result = await parse_brick_strength(project_id, node_id, context)
    
    print(f"\n返回结果:")
    print(f"  dataset_key: {result.get('dataset_key')}")
    print(f"  has_data: {result.get('meta', {}).get('has_data')}")
    print(f"  record_count: {result.get('meta', {}).get('record_count')}")
    print(f"  warnings: {result.get('meta', {}).get('warnings')}")
    
    return result


async def test_mortar_strength():
    """测试砂浆强度 API"""
    from skills_library.generation.inspection.material_strength.subskills.mortar_strength.impl.parse import parse_mortar_strength
    
    print("\n" + "=" * 80)
    print("测试砂浆强度 API")
    print("=" * 80)
    
    # 使用数据库中实际的 project_id
    project_id = "1"
    node_id = "chapter-mortar-strength"
    context = {}
    
    print(f"\n调用参数:")
    print(f"  project_id: {project_id}")
    print(f"  node_id: {node_id}")
    print(f"  context: {context}")
    
    result = await parse_mortar_strength(project_id, node_id, context)
    
    print(f"\n返回结果:")
    print(f"  dataset_key: {result.get('dataset_key')}")
    print(f"  has_data: {result.get('meta', {}).get('has_data')}")
    print(f"  record_count: {result.get('meta', {}).get('record_count')}")
    print(f"  warnings: {result.get('meta', {}).get('warnings')}")
    
    return result


async def main():
    await test_brick_strength()
    await test_mortar_strength()


if __name__ == "__main__":
    asyncio.run(main())
