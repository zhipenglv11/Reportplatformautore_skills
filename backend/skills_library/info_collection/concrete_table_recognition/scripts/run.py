#!/usr/bin/env python3
"""
统一运行入口
确保所有脚本在正确的虚拟环境中运行
"""

import os
import sys
import subprocess
import io
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (ValueError, AttributeError):
        pass


def get_venv_python():
    """获取虚拟环境的Python可执行文件路径"""
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"

    if os.name == "nt":  # Windows
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        venv_python = venv_dir / "bin" / "python"

    return venv_python


def ensure_venv():
    """确保虚拟环境存在"""
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    requirements_file = skill_dir / "requirements.txt"

    # 如果venv不存在，创建它
    if not venv_dir.exists():
        print("🔧 首次运行：创建虚拟环境...")
        print("   这可能需要几分钟...")

        # 使用系统Python创建venv
        result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
        if result.returncode != 0:
            print("❌ 创建虚拟环境失败")
            sys.exit(1)

        # 安装依赖
        venv_python = get_venv_python()
        if requirements_file.exists():
            print("📦 安装依赖...")
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
            )
            result = subprocess.run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                ],
                capture_output=True,
            )
            if result.returncode != 0:
                print("❌ 安装依赖失败")
                print(result.stderr.decode() if result.stderr else "")
                sys.exit(1)

        print("✅ 环境准备完成！")

    return get_venv_python()


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("用法: python scripts/run.py <脚本名称> [参数...]")
        print("\n可用脚本:")
        print("  batch_process.py    - 批量处理表格文件")
        print("  classify_table.py   - 分类表格类型")
        print("  extract_table.py    - 提取表格数据")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    # 处理脚本名称（支持带或不带.py扩展名）
    if script_name.startswith("scripts/"):
        script_name = script_name[8:]  # 移除 'scripts/' 前缀

    if not script_name.endswith(".py"):
        script_name += ".py"

    # 获取脚本路径
    skill_dir = Path(__file__).parent.parent
    script_path = skill_dir / "scripts" / script_name

    if not script_path.exists():
        print(f"❌ 脚本未找到: {script_name}")
        print(f"   工作目录: {Path.cwd()}")
        print(f"   技能目录: {skill_dir}")
        print(f"   查找路径: {script_path}")
        sys.exit(1)

    # 确保venv存在
    venv_python = ensure_venv()

    # 构建命令
    env = os.environ.copy()
    env["PYTHONPATH"] = str(skill_dir)
    cmd = [str(venv_python), str(script_path)] + script_args

    # 运行脚本
    try:
        result = subprocess.run(cmd, cwd=str(skill_dir), env=env, capture_output=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
