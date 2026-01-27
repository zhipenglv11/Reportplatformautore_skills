#!/usr/bin/env python3
"""
Unified entry point to run scripts with the local venv.
"""

import os
import sys
import subprocess
import io
from pathlib import Path


def get_venv_python():
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"

    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_venv():
    skill_dir = Path(__file__).parent.parent
    venv_dir = skill_dir / ".venv"
    requirements_file = skill_dir / "requirements.txt"

    if not venv_dir.exists():
        print("🔧 First run: creating virtual environment...")
        result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
        if result.returncode != 0:
            print("❌ Failed to create venv")
            sys.exit(1)

        venv_python = get_venv_python()
        if requirements_file.exists():
            print("📦 Installing dependencies...")
            subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
            )
            if result.returncode != 0:
                print("❌ Failed to install dependencies")
                print(result.stderr.decode() if result.stderr else "")
                sys.exit(1)

        print("✅ Environment ready")

    return get_venv_python()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run.py <script_name> [args...]")
        print("\nAvailable scripts:")
        print("  batch_process.py    - Batch process PDF/image files")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    if script_name.startswith("scripts/"):
        script_name = script_name[8:]

    if not script_name.endswith(".py"):
        script_name += ".py"

    skill_dir = Path(__file__).parent.parent
    script_path = skill_dir / "scripts" / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        print(f"   Working dir: {Path.cwd()}")
        print(f"   Skill dir: {skill_dir}")
        print(f"   Tried path: {script_path}")
        sys.exit(1)

    venv_python = ensure_venv()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(skill_dir)
    cmd = [str(venv_python), str(script_path)] + script_args

    try:
        result = subprocess.run(cmd, cwd=str(skill_dir), env=env, capture_output=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
