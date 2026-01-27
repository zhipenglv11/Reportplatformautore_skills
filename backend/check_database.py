#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查看数据库中所有可用的项目和数据
"""

import sys
from sqlalchemy import create_engine, text
from config import settings

def check_database():
    """检查数据库状态"""
    print("=" * 80)
    print("检查数据库中的所有项目和数据")
    print("=" * 80)
    
    db_url = settings.db_url
    if "postgresql" in db_url and "client_encoding" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}client_encoding=utf8"
    
    engine = create_engine(db_url, pool_pre_ping=True)
    
    with engine.begin() as conn:
        # 查询所有项目
        print("\n1️⃣ 所有项目 ID:")
        result = conn.execute(text("SELECT DISTINCT project_id FROM professional_data ORDER BY project_id"))
        projects = result.scalars().all()
        
        if projects:
            for project_id in projects:
                print(f"  - {project_id}")
        else:
            print("  ⚠ 没有找到任何项目!")
        
        # 查询数据统计
        print("\n2️⃣ 数据统计:")
        result = conn.execute(text("""
            SELECT 
                project_id,
                COUNT(*) as total_count,
                COUNT(DISTINCT test_item) as unique_test_items
            FROM professional_data
            GROUP BY project_id
            ORDER BY total_count DESC
        """))
        
        for row in result.all():
            print(f"  项目: {row[0]}")
            print(f"    - 总记录数: {row[1]}")
            print(f"    - 不同的 test_item: {row[2]}")
        
        # 查询所有的 test_item
        print("\n3️⃣ 所有的 test_item 类型:")
        result = conn.execute(text("""
            SELECT DISTINCT test_item, COUNT(*) as count
            FROM professional_data
            GROUP BY test_item
            ORDER BY count DESC
        """))
        
        for row in result.all():
            print(f"  - {row[0]}: {row[1]} 条")
        
        # 查询表的总行数
        print("\n4️⃣ 表统计:")
        result = conn.execute(text("SELECT COUNT(*) FROM professional_data"))
        total_rows = result.scalar()
        print(f"  professional_data 表总行数: {total_rows}")

if __name__ == "__main__":
    try:
        check_database()
        print("\n✅ 检查完成!")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
