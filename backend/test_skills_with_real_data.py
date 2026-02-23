"""
测试材料强度技能（使用真实数据库数据）
运行前需要确保数据库中有相关测试数据
"""

import asyncio
import sys
import json
from pathlib import Path

# 添加项目路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from skills_library.generation.inspection.material_strength.subskills.concrete_strength.impl.parse import parse_concrete_strength
from skills_library.generation.inspection.material_strength.subskills.brick_strength.impl.parse import parse_brick_strength
from skills_library.generation.inspection.material_strength.subskills.mortar_strength.impl.parse import parse_mortar_strength


async def test_with_real_project():
    """使用真实项目数据测试"""
    print("\n" + "="*80)
    print("请输入测试参数")
    print("="*80)
    
    project_id = input("项目ID (project_id): ").strip()
    if not project_id:
        print("❌ 项目ID不能为空")
        return
    
    node_id = input("节点ID (node_id，回车跳过使用默认): ").strip() or "material_strength_node"
    
    skill_choice = input("选择技能 (1=混凝土, 2=砖, 3=砂浆): ").strip()
    
    skill_map = {
        "1": ("concrete_strength", parse_concrete_strength, "混凝土强度"),
        "2": ("brick_strength", parse_brick_strength, "砖强度"),
        "3": ("mortar_strength", parse_mortar_strength, "砂浆强度")
    }
    
    if skill_choice not in skill_map:
        print("❌ 无效选择")
        return
    
    dataset_key, parse_func, skill_name = skill_map[skill_choice]
    
    print(f"\n{'='*80}")
    print(f"测试 {skill_name} 技能")
    print(f"项目ID: {project_id}")
    print(f"节点ID: {node_id}")
    print(f"{'='*80}\n")
    
    try:
        result = await parse_func(project_id, node_id)
        
        print("✅ 技能执行成功！\n")
        
        # 输出基本信息
        print(f"Dataset Key: {result.get('dataset_key')}")
        print(f"Has Data: {result.get('meta', {}).get('has_data', True)}")
        
        # 输出内容
        content = result.get('content', '')
        print(f"\n{'='*80}")
        print("生成的段落内容：")
        print(f"{'='*80}")
        print(content if content else "(无内容)")
        
        # 输出表格
        table = result.get('table', {})
        print(f"\n{'='*80}")
        print("生成的表格：")
        print(f"{'='*80}")
        if table.get('columns') and table.get('rows'):
            print(f"列: {table['columns']}")
            print(f"行数: {len(table['rows'])}")
            print("\n前3行数据：")
            for i, row in enumerate(table['rows'][:3], 1):
                print(f"  {i}. {row}")
        else:
            print("(无表格数据)")
        
        # 输出元信息
        meta = result.get('meta', {})
        print(f"\n{'='*80}")
        print("元信息：")
        print(f"{'='*80}")
        print(f"来源: {meta.get('source')}")
        print(f"材料类型: {meta.get('material_type')}")
        print(f"检测数量: {meta.get('test_count')}")
        print(f"检测方法: {meta.get('test_method')}")
        print(f"平均强度: {meta.get('avg_strength')} {meta.get('strength_unit', 'MPa')}")
        print(f"强度范围: {meta.get('strength_range')}")
        print(f"警告信息: {meta.get('warnings', [])}")
        
        # 保存完整结果到文件
        output_file = f"test_result_{dataset_key}_{project_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 完整结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  材料强度技能 - 真实数据测试工具                            ║
╚════════════════════════════════════════════════════════════════════════════╝

使用说明：
1. 确保数据库中已有 professional_data 表的测试数据
2. 数据需要包含对应的 test_item (如 '混凝土强度检测')
3. 输入正确的 project_id 和 node_id

""")
    
    await test_with_real_project()


if __name__ == "__main__":
    asyncio.run(main())
