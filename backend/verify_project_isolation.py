# -*- coding: utf-8 -*-
"""
验证容错逻辑不会跨项目查询数据
"""

import asyncio
from sqlalchemy import create_engine, text
from config import settings

async def verify_project_isolation():
    """验证 project_id 隔离是否正常工作"""
    from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
    
    # 先检查数据库中有哪些 project_id
    engine = create_engine(settings.db_url)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT project_id, COUNT(*) as count
            FROM professional_data
            WHERE test_item LIKE '%brick%' OR test_item LIKE '%砖%'
            GROUP BY project_id
            ORDER BY project_id
        """))
        
        print("=" * 80)
        print("数据库中的砖强度数据分布：")
        print("=" * 80)
        for row in result:
            print(f"  Project ID: {row.project_id}, 记录数: {row.count}")
    
    print("\n" + "=" * 80)
    print("测试容错逻辑的 project_id 隔离：")
    print("=" * 80)
    
    # 测试 project_id = "1"（存在数据）
    print("\n1. 查询 project_id='1' (错误的 source_node_id):")
    context = {"source_node_id": "wrong-node-id"}
    result = await parse_brick_strength("1", "test-node", context)
    print(f"   找到记录数: {result.get('meta', {}).get('record_count')}")
    
    # 测试 project_id = "999"（不存在的项目）
    print("\n2. 查询 project_id='999' (不存在的项目):")
    context = {"source_node_id": "wrong-node-id"}
    result = await parse_brick_strength("999", "test-node", context)
    print(f"   找到记录数: {result.get('meta', {}).get('record_count')}")
    print(f"   has_data: {result.get('meta', {}).get('has_data')}")
    
    # 测试 project_id = "2"（如果存在）
    print("\n3. 查询 project_id='2' (如果该项目无砖数据):")
    context = {"source_node_id": "wrong-node-id"}
    result = await parse_brick_strength("2", "test-node", context)
    print(f"   找到记录数: {result.get('meta', {}).get('record_count')}")
    print(f"   has_data: {result.get('meta', {}).get('has_data')}")
    
    print("\n" + "=" * 80)
    print("结论：")
    print("如果 project_id='1' 能找到数据，而 '999' 和 '2' 找不到，")
    print("说明容错逻辑正确保留了 project_id 过滤条件，不会跨项目查询。")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(verify_project_isolation())
