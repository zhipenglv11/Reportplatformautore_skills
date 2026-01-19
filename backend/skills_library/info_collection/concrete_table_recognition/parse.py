#!/usr/bin/env python3
"""
混凝土表格识别主入口脚本
作为 Claude Skills 的标准化入口点
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from scripts.batch_process import main

if __name__ == "__main__":
    main()
