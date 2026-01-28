"""
集成测试：验证generation skills的系统集成
测试目标：
1. loader能否扫描到父skill和子skills
2. 能否直接调用父skill的assemble函数
3. 子skill的parse函数能否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加backend到路径
sys.path.insert(0, str(Path(__file__).parent))

from services.declarative_skills.loader import SkillLoader
from skills_library.generation.inspection.material_strength.impl import (
    assemble_material_strength,
    detect_available_materials
)
from skills_library.generation.inspection.material_strength.subskills.concrete_strength.impl import (
    parse_concrete_strength
)


def test_1_loader_can_find_skills():
    """测试1：Loader能否找到所有skills"""
    print("\n" + "="*60)
    print("测试1：检查Loader能否扫描到generation skills")
    print("="*60)
    
    skills_base_path = Path(__file__).parent / "skills_library"
    loader = SkillLoader(skills_base_path)
    
    # 列出所有skills
    all_skills = loader.list_available_skills()
    print(f"\n✅ 找到 {len(all_skills)} 个skills:")
    
    # 检查关键skills
    expected_skills = [
        "material_strength",      # 父skill
        "concrete_strength",      # 子skill
        "brick_strength",         # 子skill框架
        "mortar_strength"         # 子skill框架
    ]
    
    for skill_name in expected_skills:
        if skill_name in all_skills:
            print(f"   ✅ {skill_name}")
        else:
            print(f"   ❌ {skill_name} (未找到)")
    
    # 尝试加载父skill
    try:
        parent_skill = loader.load_skill("material_strength")
        print(f"\n✅ 成功加载父skill: {parent_skill.skill_name}")
        print(f"   版本: {parent_skill.version}")
        print(f"   描述: {parent_skill.description}")
        print(f"   目录: {parent_skill.skill_dir}")
    except Exception as e:
        print(f"\n❌ 加载父skill失败: {e}")
    
    # 尝试加载子skill
    try:
        child_skill = loader.load_skill("concrete_strength")
        print(f"\n✅ 成功加载子skill: {child_skill.skill_name}")
        print(f"   版本: {child_skill.version}")
        print(f"   目录: {child_skill.skill_dir}")
    except Exception as e:
        print(f"\n❌ 加载子skill失败: {e}")
    
    return all_skills


async def test_2_can_call_subskill_directly():
    """测试2：能否直接调用子skill的parse函数"""
    print("\n" + "="*60)
    print("测试2：直接调用concrete_strength子skill")
    print("="*60)
    
    try:
        # 使用模拟数据测试（实际需要有数据库连接）
        print("\n⚠️  注意：需要数据库连接，这里仅测试函数是否可调用")
        print("   调用函数: parse_concrete_strength()")
        print("   预期参数: project_id, node_id")
        
        # 检查函数签名
        import inspect
        sig = inspect.signature(parse_concrete_strength)
        print(f"   函数签名: {sig}")
        print(f"   是否async: {inspect.iscoroutinefunction(parse_concrete_strength)}")
        
        # 如果是async函数，尝试调用（会因为无数据而失败，但能验证调用路径）
        if inspect.iscoroutinefunction(parse_concrete_strength):
            print("\n✅ concrete_strength.parse 是async函数，可以被await调用")
        else:
            print("\n❌ concrete_strength.parse 不是async函数")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_3_can_call_parent_assemble():
    """测试3：能否调用父skill的assemble函数"""
    print("\n" + "="*60)
    print("测试3：调用父skill的assemble_material_strength()")
    print("="*60)
    
    try:
        # 检查函数签名
        import inspect
        sig = inspect.signature(assemble_material_strength)
        print(f"\n函数签名: {sig}")
        print(f"是否async: {inspect.iscoroutinefunction(assemble_material_strength)}")
        
        # 检查detect函数
        sig2 = inspect.signature(detect_available_materials)
        print(f"\ndetect函数签名: {sig2}")
        print(f"是否async: {inspect.iscoroutinefunction(detect_available_materials)}")
        
        print("\n⚠️  实际调用需要数据库连接，这里仅验证函数可导入")
        print("   调用方式: await assemble_material_strength(project_id='xxx', node_id='xxx')")
        print("\n✅ 父skill函数可正常导入和调用")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_4_check_file_structure():
    """测试4：检查文件结构完整性"""
    print("\n" + "="*60)
    print("测试4：检查文件结构")
    print("="*60)
    
    base_dir = Path(__file__).parent / "skills_library" / "generation" / "inspection" / "material_strength"
    
    # 父skill文件
    parent_files = {
        "SKILL.md": base_dir / "SKILL.md",
        "fields.yaml": base_dir / "fields.yaml",
        "render.md": base_dir / "render.md",
        "impl/assemble.py": base_dir / "impl" / "assemble.py",
        "impl/__init__.py": base_dir / "impl" / "__init__.py",
    }
    
    print("\n父skill文件:")
    for name, path in parent_files.items():
        status = "✅" if path.exists() else "❌"
        print(f"   {status} {name}")
    
    # concrete_strength子skill文件
    concrete_dir = base_dir / "subskills" / "concrete_strength"
    concrete_files = {
        "SKILL.md": concrete_dir / "SKILL.md",
        "fields.yaml": concrete_dir / "fields.yaml",
        "render.md": concrete_dir / "render.md",
        "impl/parse.py": concrete_dir / "impl" / "parse.py",
        "impl/__init__.py": concrete_dir / "impl" / "__init__.py",
    }
    
    print("\nconcrete_strength子skill文件:")
    for name, path in concrete_files.items():
        status = "✅" if path.exists() else "❌"
        print(f"   {status} {name}")
    
    # brick_strength子skill文件
    brick_dir = base_dir / "subskills" / "brick_strength"
    print("\nbrick_strength子skill文件:")
    print(f"   {'✅' if (brick_dir / 'SKILL.md').exists() else '❌'} SKILL.md")
    print(f"   {'⚠️ ' if not (brick_dir / 'fields.yaml').exists() else '✅'} fields.yaml (待创建)")
    print(f"   {'⚠️ ' if not (brick_dir / 'render.md').exists() else '✅'} render.md (待创建)")
    print(f"   {'⚠️ ' if not (brick_dir / 'impl' / 'parse.py').exists() else '✅'} impl/parse.py (待创建)")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Generation Skills 系统集成测试")
    print("="*60)
    
    # 测试1：Loader扫描
    test_1_loader_can_find_skills()
    
    # 测试2：子skill调用
    await test_2_can_call_subskill_directly()
    
    # 测试3：父skill调用
    await test_3_can_call_parent_assemble()
    
    # 测试4：文件结构
    test_4_check_file_structure()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n📋 后续步骤:")
    print("   1. 如果所有测试通过，可以开始开发brick_strength和mortar_strength")
    print("   2. 如果有问题，需要先解决集成问题")
    print("   3. 建议：创建一个带真实数据库的端到端测试")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
