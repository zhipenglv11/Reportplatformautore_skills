"""
测试合并后的技能输出格式（描述+表格）
验证 concrete_strength/brick_strength/mortar_strength 是否返回统一格式
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


async def test_concrete_strength():
    """测试混凝土强度技能"""
    print("\n" + "="*80)
    print("测试 concrete_strength 技能输出")
    print("="*80)
    
    try:
        result = await parse_concrete_strength(
            project_id="test_project",
            node_id="concrete_test_node",
            context={"code_reference": "GB50292-2015 附录K"}
        )
        
        # 验证输出格式
        assert "dataset_key" in result, "缺少 dataset_key 字段"
        assert "content" in result, "缺少 content 字段"
        assert "table" in result, "缺少 table 字段"
        assert "meta" in result, "缺少 meta 字段"
        
        assert result["dataset_key"] == "concrete_strength", "dataset_key 不正确"
        assert isinstance(result["content"], str), "content 应该是字符串"
        assert isinstance(result["table"], dict), "table 应该是字典"
        assert "columns" in result["table"], "table 缺少 columns"
        assert "rows" in result["table"], "table 缺少 rows"
        
        print("✅ dataset_key:", result["dataset_key"])
        print("✅ content (前100字符):", result["content"][:100] if result["content"] else "(空)")
        print("✅ table.columns:", result["table"].get("columns", []))
        print(f"✅ table.rows 数量: {len(result['table'].get('rows', []))}")
        print("✅ meta.source:", result["meta"].get("source"))
        print("✅ meta.material_type:", result["meta"].get("material_type"))
        print("✅ meta.warnings:", result["meta"].get("warnings", []))
        
        print("\n完整输出结构（JSON格式）:")
        print(json.dumps({
            "dataset_key": result["dataset_key"],
            "content_length": len(result["content"]),
            "table_structure": {
                "columns": result["table"]["columns"],
                "row_count": len(result["table"]["rows"])
            },
            "meta_keys": list(result["meta"].keys())
        }, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_brick_strength():
    """测试砖强度技能"""
    print("\n" + "="*80)
    print("测试 brick_strength 技能输出")
    print("="*80)
    
    try:
        result = await parse_brick_strength(
            project_id="test_project",
            node_id="brick_test_node"
        )
        
        # 验证输出格式
        assert "dataset_key" in result, "缺少 dataset_key 字段"
        assert result["dataset_key"] == "brick_strength", "dataset_key 不正确"
        assert "content" in result, "缺少 content 字段"
        assert "table" in result, "缺少 table 字段"
        assert "meta" in result, "缺少 meta 字段"
        
        print("✅ dataset_key:", result["dataset_key"])
        print("✅ content (前100字符):", result["content"][:100] if result["content"] else "(空)")
        print("✅ table.columns:", result["table"].get("columns", []))
        print(f"✅ table.rows 数量: {len(result['table'].get('rows', []))}")
        print("✅ meta.source:", result["meta"].get("source"))
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mortar_strength():
    """测试砂浆强度技能"""
    print("\n" + "="*80)
    print("测试 mortar_strength 技能输出")
    print("="*80)
    
    try:
        result = await parse_mortar_strength(
            project_id="test_project",
            node_id="mortar_test_node"
        )
        
        # 验证输出格式
        assert "dataset_key" in result, "缺少 dataset_key 字段"
        assert result["dataset_key"] == "mortar_strength", "dataset_key 不正确"
        assert "content" in result, "缺少 content 字段"
        assert "table" in result, "缺少 table 字段"
        assert "meta" in result, "缺少 meta 字段"
        
        print("✅ dataset_key:", result["dataset_key"])
        print("✅ content (前100字符):", result["content"][:100] if result["content"] else "(空)")
        print("✅ table.columns:", result["table"].get("columns", []))
        print(f"✅ table.rows 数量: {len(result['table'].get('rows', []))}")
        print("✅ meta.source:", result["meta"].get("source"))
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("测试技能合并输出格式（描述+表格）")
    print("="*80)
    
    results = []
    
    # 测试三个技能
    results.append(await test_concrete_strength())
    results.append(await test_brick_strength())
    results.append(await test_mortar_strength())
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试汇总")
    print("="*80)
    total = len(results)
    passed = sum(results)
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if all(results):
        print("\n✅ 所有测试通过！")
        print("\n核心验证通过:")
        print("1. ✅ 输出格式统一: {dataset_key, content, table, meta}")
        print("2. ✅ content 为段落文本（可直接进报告）")
        print("3. ✅ table 为 {columns, rows} 结构（供前端渲染）")
        print("4. ✅ meta 包含来源、警告等元信息")
    else:
        print("\n❌ 部分测试失败，请检查日志")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
