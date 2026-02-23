# -*- coding: utf-8 -*-
"""脚本执行器：执行声明式 Skills 的脚本"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class ScriptRunner:
    """执行声明式 Skills 的脚本"""

    def __init__(self, skill_dir: Path):
        """
        初始化脚本执行器
        
        Args:
            skill_dir: 技能目录路径
        """
        self.skill_dir = skill_dir
        self._python_executable = self._resolve_python_executable()

    def _resolve_python_executable(self) -> str:
        """解析 Python 可执行文件路径
        
        优先级：
        1. 环境变量 SKILL_PYTHON
        2. 当前 skill 目录下的虚拟环境 (.venv)
        3. 项目根目录下的虚拟环境 (.venv) - 适用于没有独立虚拟环境的 skills
        4. 系统 Python (sys.executable)
        """
        env_python = os.getenv("SKILL_PYTHON")
        if env_python:
            return env_python
        
        # 1. 查找当前 skill 目录下的虚拟环境
        venv_candidates = [
            self.skill_dir / ".venv" / "Scripts" / "python.exe",
            self.skill_dir / "venv" / "Scripts" / "python.exe",
            self.skill_dir / ".venv" / "bin" / "python",
            self.skill_dir / "venv" / "bin" / "python",
        ]
        for candidate in venv_candidates:
            if candidate.exists():
                return str(candidate)
        
        # 2. 查找项目根目录下的虚拟环境（向上3级）
        # backend/skills_library/info_collection/skill_name -> backend
        project_root = self.skill_dir.parent.parent.parent.parent
        root_venv_candidates = [
            project_root / ".venv" / "Scripts" / "python.exe",
            project_root / ".venv" / "bin" / "python",
        ]
        for candidate in root_venv_candidates:
            if candidate.exists():
                return str(candidate)
        
        # 3. 使用系统 Python
        return sys.executable

    def run_script(
        self,
        script_name: str = "parse.py",
        args: Optional[list] = None,
        input_data: Optional[Dict[str, Any]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        执行脚本
        
        Args:
            script_name: 脚本文件名（如 "parse.py"）
            args: 命令行参数列表
            input_data: 输入数据（通过 stdin 传递，JSON 格式）
            env: 额外的环境变量
            timeout: 超时时间（秒），默认 5 分钟
        
        Returns:
            执行结果字典，包含：
            - success: bool - 是否成功
            - returncode: int - 返回码
            - output: Any - 输出内容（尝试解析为 JSON）
            - stdout: str - 标准输出
            - stderr: str - 标准错误
            - error: str - 错误信息（如果有）
        """
        script_path = self.skill_dir / script_name
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
            }

        # 构建命令
        cmd = [self._python_executable, str(script_path)]
        if args:
            cmd.extend(args)

        # 构建环境变量
        script_env = dict(os.environ)
        
        # 将技能目录添加到 PYTHONPATH，确保脚本可以导入 scripts 模块
        pythonpath = str(self.skill_dir)
        if "PYTHONPATH" in script_env:
            pythonpath = f"{pythonpath}{os.pathsep}{script_env['PYTHONPATH']}"
        script_env["PYTHONPATH"] = pythonpath
        
        if env:
            script_env.update(env)

        # 准备输入数据
        stdin_data = None
        if input_data:
            try:
                stdin_data = json.dumps(input_data, ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError) as e:
                return {
                    "success": False,
                    "error": f"Failed to serialize input_data: {e}",
                }

        # 执行脚本
        try:
            process = subprocess.run(
                cmd,
                cwd=str(self.skill_dir),
                input=stdin_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # 使用字节模式，避免编码问题
                timeout=timeout,
                env=script_env,
            )

            # 解码输出
            stdout = process.stdout.decode("utf-8", errors="replace")
            stderr = process.stderr.decode("utf-8", errors="replace")

            # 尝试解析 JSON 输出
            output = None
            if stdout.strip():
                try:
                    output = json.loads(stdout)
                except json.JSONDecodeError:
                    # 如果不是 JSON，保留原始输出
                    output = stdout

            result = {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": output,
                "stdout": stdout,
                "stderr": stderr,
                "python": self._python_executable,
            }

            if process.returncode != 0:
                error_message = f"Script exited with code {process.returncode}"
                if "ModuleNotFoundError" in stderr:
                    error_message = f"{error_message}; missing dependency (ModuleNotFoundError)"
                result["error"] = error_message

            return result

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Script execution timeout ({timeout}s)",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}",
            }
