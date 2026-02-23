# -*- coding: utf-8 -*-
"""
临时脚本：详细检查砖和砂浆数据
"""

from sqlalchemy import create_engine, text
from config import settings

def check_brick_mortar_details():
    engine = create_engine(settings.db_url)
    
    with engine.connect() as conn:
        print("=" * 80)
        print("砖强度 (brick_table_recognition) 记录详情:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT 
                id,
                project_id,
                node_id,
                test_item,
                CASE 
                    WHEN confirmed_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_confirmed_result,
                CASE 
                    WHEN raw_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_raw_result,
                CASE 
                    WHEN test_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_test_result,
                strength_estimated_mpa,
                created_at
            FROM professional_data
            WHERE test_item = 'brick_table_recognition'
            ORDER BY created_at DESC
        """))
        
        for row in result:
            print(f"\nID: {row.id}")
            print(f"  Project ID: {row.project_id}")
            print(f"  Node ID: {row.node_id}")
            print(f"  Has confirmed_result: {row.has_confirmed_result}")
            print(f"  Has raw_result: {row.has_raw_result}")
            print(f"  Has test_result: {row.has_test_result}")
            print(f"  Strength (MPa): {row.strength_estimated_mpa}")
            print(f"  Created: {row.created_at}")
        
        print("\n" + "=" * 80)
        print("砂浆强度 (mortar_table_recognition) 记录详情:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT 
                id,
                project_id,
                node_id,
                test_item,
                CASE 
                    WHEN confirmed_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_confirmed_result,
                CASE 
                    WHEN raw_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_raw_result,
                CASE 
                    WHEN test_result IS NOT NULL THEN 'YES'
                    ELSE 'NO'
                END as has_test_result,
                strength_estimated_mpa,
                created_at
            FROM professional_data
            WHERE test_item = 'mortar_table_recognition'
            ORDER BY created_at DESC
        """))
        
        for row in result:
            print(f"\nID: {row.id}")
            print(f"  Project ID: {row.project_id}")
            print(f"  Node ID: {row.node_id}")
            print(f"  Has confirmed_result: {row.has_confirmed_result}")
            print(f"  Has raw_result: {row.has_raw_result}")
            print(f"  Has test_result: {row.has_test_result}")
            print(f"  Strength (MPa): {row.strength_estimated_mpa}")
            print(f"  Created: {row.created_at}")
        
        # 检查满足完整查询条件的记录数
        print("\n" + "=" * 80)
        print("满足完整查询条件的砖强度记录数:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM professional_data
            WHERE (
                LOWER(test_item) LIKE '%brick%'
                OR test_item = 'brick_table_recognition'
                OR test_item = 'brick_strength'
                OR test_item LIKE '%砖%'
            )
            AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        """))
        count = result.fetchone()
        print(f"  总计: {count.count} 条记录")
        
        print("\n" + "=" * 80)
        print("满足完整查询条件的砂浆强度记录数:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM professional_data
            WHERE (
                LOWER(test_item) LIKE '%mortar%'
                OR test_item = 'mortar_table_recognition'
                OR test_item = 'mortar_strength'
                OR test_item LIKE '%砂浆%'
            )
            AND (confirmed_result IS NOT NULL OR raw_result IS NOT NULL)
        """))
        count = result.fetchone()
        print(f"  总计: {count.count} 条记录")

if __name__ == "__main__":
    check_brick_mortar_details()
