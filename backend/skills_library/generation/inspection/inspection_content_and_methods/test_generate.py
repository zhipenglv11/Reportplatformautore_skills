"""
测试鉴定内容和方法生成器
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from skills_library.generation.inspection.inspection_content_and_methods.impl import (
    generate_inspection_content_and_methods
)
import json


def test_generate():
    """测试生成功能"""
    print("=" * 80)
    print("测试：生成鉴定内容和方法及原始记录一览表")
    print("=" * 80)
    
    result = generate_inspection_content_and_methods(
        project_id="test-project",
        node_id="test-node",
        context={"chapter_number": "三"}
    )
    
    print(f"\n章节: {result['chapter_number']}、{result['chapter_title']}")
    print(f"状态: {'有数据' if result['has_data'] else '无数据'}")
    print(f"生成时间: {result['generation_metadata']['generated_at']}")
    
    for section in result['sections']:
        print("\n" + "=" * 80)
        print(f"{section['section_number']} {section['section_title']}")
        print("=" * 80)
        
        if section['type'] == 'text':
            print(section['content'])
        
        elif section['type'] == 'table':
            table = section['table']
            print(f"\n表格包含 {len(table['rows'])} 行数据：")
            
            # 打印表头
            headers = [col['label'] for col in table['columns']]
            print("\n" + " | ".join(headers))
            print("-" * 80)
            
            # 打印数据行
            for row in table['rows']:
                values = []
                for col in table['columns']:
                    key = col['key']
                    values.append(str(row.get(key, '')))
                print(" | ".join(values))
    
    print("\n" + "=" * 80)
    print("完整 JSON 输出：")
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_generate()
