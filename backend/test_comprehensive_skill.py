#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：诊断混凝土强度综合规则的问题
"""

import sys
import json
from models.db import fetch_professional_data

def test_data_fetch(project_id: str, node_id: str = None):
    """测试数据库查询"""
    print("=" * 80)
    print("测试数据库查询")
    print("=" * 80)
    
    records = fetch_professional_data(
        project_id=project_id,
        node_id=node_id,
        test_item=None,
    )
    
    print(f"✓ 总记录数: {len(records)}")
    
    if not records:
        print("⚠ 警告: 没有找到任何记录！")
        return False
    
    # 统计 test_item 的分布
    test_items_count = {}
    for record in records:
        test_item = record.get("test_item")
        test_items_count[test_item] = test_items_count.get(test_item, 0) + 1
    
    print("\n✓ test_item 分布:")
    for test_item, count in sorted(test_items_count.items(), key=lambda x: -x[1]):
        print(f"  - {test_item}: {count} 条")
    
    # 显示第一条记录的详细信息
    print("\n✓ 第一条记录的详细信息:")
    first_record = records[0]
    for key in ["test_item", "test_value_json", "raw_result", "design_strength_grade", "strength_estimated_mpa"]:
        value = first_record.get(key)
        if isinstance(value, (dict, list)):
            print(f"  {key}: {json.dumps(value, ensure_ascii=False, indent=4)}")
        else:
            print(f"  {key}: {value}")
    
    return True


def test_dataset_matching(test_items: list, dataset_test_items: list):
    """测试 dataset 匹配"""
    print("\n" + "=" * 80)
    print("测试数据集匹配")
    print("=" * 80)
    
    print(f"数据库中的 test_item: {test_items}")
    print(f"Dataset 中定义的 test_items: {dataset_test_items}")
    
    def matches_test_items(test_item: str) -> bool:
        if not test_item:
            return False
        test_item_lower = test_item.lower()
        # 精确匹配
        for item in dataset_test_items:
            if test_item_lower == item.lower():
                return True
        # 包含匹配
        for item in dataset_test_items:
            if item.lower() in test_item_lower or test_item_lower in item.lower():
                return True
        return False
    
    print("\n✓ 匹配结果:")
    matched_count = 0
    for test_item in test_items:
        result = matches_test_items(test_item)
        symbol = "✅" if result else "❌"
        print(f"  {symbol} {test_item}: {result}")
        if result:
            matched_count += 1
    
    print(f"\n✓ 匹配数: {matched_count}/{len(test_items)}")


def main():
    """主函数"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 使用实际存在的项目ID
    project_id = "1"  # 这个项目在数据库中有数据
    node_id = None
    
    print(f"🔍 开始诊断")
    print(f"  项目ID: {project_id}")
    print(f"  节点ID: {node_id}\n")
    
    # 测试数据获取
    success = test_data_fetch(project_id, node_id)
    
    if success:
        # 获取 test_item 列表进行匹配测试
        records = fetch_professional_data(project_id=project_id, node_id=node_id, test_item=None)
        test_items = list(set(r.get("test_item") for r in records if r.get("test_item")))
        
        # Dataset 中定义的 test_items（已更新）
        dataset_test_items = ["混凝土抗压强度", "混凝土强度", "混凝土强度检测表格", "concrete_table_recognition"]
        
        test_dataset_matching(test_items, dataset_test_items)
        
        print("\n" + "=" * 80)
        print("💡 下一步:")
        print("=" * 80)
        print("如果匹配数 > 0，说明数据可以被成功匹配！")
        print("现在可以尝试在前端生成报告了。")
    
    print("\n✅ 诊断完成！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
