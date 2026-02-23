"""
测试动态数据提取功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from skills_library.generation.inspection.inspection_content_and_methods.impl import (
    generate_inspection_content_and_methods
)
from skills_library.generation.inspection.inspection_content_and_methods.impl.extract_utils import (
    extract_instruments_from_db,
    extract_records_from_db
)
import json


def test_extract_instruments():
    """测试仪器设备提取"""
    print("=" * 80)
    print("测试：提取仪器设备信息")
    print("=" * 80)
    
    # 这里使用一个示例 project_id，需要实际数据库中有数据
    project_id = "test-project"
    
    try:
        instruments = extract_instruments_from_db(project_id)
        
        print(f"\n提取到 {len(instruments)} 个仪器设备：\n")
        
        for i, inst in enumerate(instruments, 1):
            print(f"{i}. {inst.get('instrument_name', 'N/A')}")
            print(f"   规格型号: {inst.get('model', 'N/A')}")
            print(f"   编号: {inst.get('serial_number', 'N/A')}")
            print(f"   有效期: {inst.get('valid_until', 'N/A')}")
            print()
    
    except Exception as e:
        print(f"错误: {e}")


def test_extract_records():
    """测试原始记录提取"""
    print("=" * 80)
    print("测试：提取原始记录清单")
    print("=" * 80)
    
    project_id = "test-project"
    
    try:
        records = extract_records_from_db(project_id)
        
        print(f"\n提取到 {len(records)} 条原始记录：\n")
        
        for i, rec in enumerate(records, 1):
            print(f"{i}. {rec.get('record_name', 'N/A')}: {rec.get('internal_number', 'N/A')}")
    
    except Exception as e:
        print(f"错误: {e}")


def test_generate_with_dynamic_data():
    """测试使用动态数据生成章节"""
    print("\n" + "=" * 80)
    print("测试：生成章节（动态数据模式）")
    print("=" * 80)
    
    project_id = "test-project"
    node_id = "test-node"
    
    result = generate_inspection_content_and_methods(
        project_id=project_id,
        node_id=node_id,
        context={
            "chapter_number": "三",
            "use_dynamic_data": True  # 启用动态数据
        }
    )
    
    print(f"\n章节: {result['chapter_number']}、{result['chapter_title']}")
    print(f"数据模式: {'动态' if result['generation_metadata']['use_dynamic_data'] else '静态'}")
    
    for section in result['sections']:
        print(f"\n{section['section_number']} {section['section_title']}")
        
        if section['type'] == 'table':
            data_source = section.get('data_source', 'unknown')
            row_count = len(section['table']['rows'])
            print(f"  数据来源: {data_source}")
            print(f"  数据行数: {row_count}")


def test_generate_with_static_data():
    """测试使用静态数据生成章节"""
    print("\n" + "=" * 80)
    print("测试：生成章节（静态数据模式）")
    print("=" * 80)
    
    result = generate_inspection_content_and_methods(
        project_id="test-project",
        node_id="test-node",
        context={
            "chapter_number": "三",
            "use_dynamic_data": False  # 使用静态数据
        }
    )
    
    print(f"\n章节: {result['chapter_number']}、{result['chapter_title']}")
    print(f"数据模式: {'动态' if result['generation_metadata']['use_dynamic_data'] else '静态'}")
    
    for section in result['sections']:
        if section['type'] == 'table':
            print(f"\n{section['section_number']} {section['section_title']}")
            data_source = section.get('data_source', 'unknown')
            row_count = len(section['table']['rows'])
            print(f"  数据来源: {data_source}")
            print(f"  数据行数: {row_count}")


if __name__ == "__main__":
    print("\n" + "🧪 开始测试动态数据提取功能" + "\n")
    
    # 测试1：提取仪器设备
    test_extract_instruments()
    
    # 测试2：提取原始记录
    test_extract_records()
    
    # 测试3：动态数据模式生成
    test_generate_with_dynamic_data()
    
    # 测试4：静态数据模式生成
    test_generate_with_static_data()
    
    print("\n" + "✅ 测试完成" + "\n")
