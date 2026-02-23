# -*- coding: utf-8 -*-
"""
测试脚本执行器是否能正确解析 Python 可执行文件
"""

from pathlib import Path
import sys

# 添加 backend 到 path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.declarative_skills.script_runner import ScriptRunner

# 测试不同的 skill 目录
test_skills = [
    "skills_library/info_collection/brick_table_recognition",
    "skills_library/info_collection/mortar_table_recognition",
    "skills_library/info_collection/structure_damage_alterations_recognition",
    "skills_library/info_collection/concrete_table_recognition",
]

print("=" * 80)
print("测试脚本执行器的 Python 可执行文件解析")
print("=" * 80)

for skill_path in test_skills:
    skill_dir = backend_dir / skill_path
    if not skill_dir.exists():
        print(f"\n✗ Skill 目录不存在: {skill_path}")
        continue
    
    print(f"\n{skill_path}:")
    print(f"  Skill 目录: {skill_dir}")
    
    # 检查是否有自己的虚拟环境
    has_own_venv = (skill_dir / ".venv").exists() or (skill_dir / "venv").exists()
    print(f"  有独立虚拟环境: {has_own_venv}")
    
    # 创建 ScriptRunner 并解析 Python 可执行文件
    runner = ScriptRunner(skill_dir)
    python_exe = runner._python_executable
    python_path = Path(python_exe)
    
    print(f"  使用的 Python: {python_exe}")
    print(f"  Python 存在: {python_path.exists()}")
    
    # 检测是项目根目录的 venv 还是 skill 自己的 venv
    if str(backend_dir.parent / ".venv") in str(python_exe):
        print(f"  ✓ 使用项目根目录虚拟环境")
    elif ".venv" in str(python_exe) or "venv" in str(python_exe):
        print(f"  ✓ 使用 Skill 独立虚拟环境")
    else:
        print(f"  ⚠ 使用系统 Python")
    
    # 测试是否能导入关键依赖
    if python_path.exists():
        import subprocess
        result = subprocess.run(
            [str(python_exe), "-c", "import dashscope; print('dashscope OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  ✓ dashscope 可用")
        else:
            print(f"  ✗ dashscope 不可用")
            if "ModuleNotFoundError" in result.stderr:
                print(f"    错误: ModuleNotFoundError")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
