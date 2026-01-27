#!/usr/bin/env python3
"""
Structure Damage and Alterations Extraction - Main Entry Point
结构损伤及拆改检查数据抽取 - 主入口文件

This is the main executable entry point for the structure damage and alterations extraction skill.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.run import main as run_main


def main():
    """Main entry point for the structure damage and alterations extraction skill."""
    parser = argparse.ArgumentParser(
        description="从结构损伤及拆改检查原始记录中提取结构化数据",
        epilog="示例: python parse.py input.pdf -o output/ -f json"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='要处理的 PDF 或图片文件'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='data/output',
        help='输出目录 (默认: data/output)'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['json', 'csv', 'excel', 'all'],
        default='json',
        help='输出格式 (默认: json)'
    )
    parser.add_argument(
        '--model',
        '-m',
        choices=['claude', 'qwen'],
        help='使用的模型 (覆盖配置文件设置)'
    )
    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version='Structure Damage and Alterations Extractor v1.0.0'
    )

    args = parser.parse_args()

    # 检查文件是否存在
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"错误: 文件不存在: {file_path}")
            sys.exit(1)

    # Call the actual processing function
    run_main(args)


if __name__ == '__main__':
    main()
