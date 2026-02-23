# -*- coding: utf-8 -*-
"""
临时脚本：检查数据库中的砖和砂浆数据
"""

from sqlalchemy import create_engine, text
from config import settings

def check_data():
    engine = create_engine(settings.db_url)
    
    with engine.connect() as conn:
        # 查询所有 test_item 的值
        print("=" * 80)
        print("所有不重复的 test_item 值:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT DISTINCT test_item, COUNT(*) as count
            FROM professional_data
            GROUP BY test_item
            ORDER BY count DESC
        """))
        
        for row in result:
            print(f"  {row.test_item}: {row.count} 条记录")
        
        print("\n" + "=" * 80)
        print("查找包含'砖'或'brick'的记录:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT test_item, COUNT(*) as count
            FROM professional_data
            WHERE LOWER(test_item) LIKE '%brick%' OR test_item LIKE '%砖%'
            GROUP BY test_item
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"  {row.test_item}: {row.count} 条记录")
        else:
            print("  未找到相关记录")
        
        print("\n" + "=" * 80)
        print("查找包含'砂浆'或'mortar'的记录:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT test_item, COUNT(*) as count
            FROM professional_data
            WHERE LOWER(test_item) LIKE '%mortar%' OR test_item LIKE '%砂浆%'
            GROUP BY test_item
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"  {row.test_item}: {row.count} 条记录")
        else:
            print("  未找到相关记录")
        
        print("\n" + "=" * 80)
        print("查找包含'混凝土'或'concrete'的记录:")
        print("=" * 80)
        result = conn.execute(text("""
            SELECT test_item, COUNT(*) as count
            FROM professional_data
            WHERE LOWER(test_item) LIKE '%concrete%' OR test_item LIKE '%混凝土%'
            GROUP BY test_item
        """))
        
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"  {row.test_item}: {row.count} 条记录")
        else:
            print("  未找到相关记录")
        
        # 查询总记录数
        print("\n" + "=" * 80)
        print("professional_data 表总记录数:")
        print("=" * 80)
        result = conn.execute(text("SELECT COUNT(*) as total FROM professional_data"))
        total = result.fetchone()
        print(f"  总计: {total.total} 条记录")
        
        # 如果记录很少，显示所有记录的详细信息
        if total.total > 0 and total.total <= 20:
            print("\n" + "=" * 80)
            print("所有记录的详细信息:")
            print("=" * 80)
            result = conn.execute(text("""
                SELECT id, project_id, node_id, test_item, 
                       SUBSTR(test_result, 1, 50) as test_result_preview,
                       created_at
                FROM professional_data
                ORDER BY created_at DESC
            """))
            
            for row in result:
                print(f"\nID: {row.id}")
                print(f"  Project ID: {row.project_id}")
                print(f"  Node ID: {row.node_id}")
                print(f"  Test Item: {row.test_item}")
                print(f"  Test Result: {row.test_result_preview}...")
                print(f"  Created At: {row.created_at}")

if __name__ == "__main__":
    check_data()
