#!/usr/bin/env python3
"""
Mortar Strength Extraction - Main Entry Point
砂浆强度检测数据抽取 - 主入口文件

This is the main executable entry point for the mortar strength extraction skill.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.run import main as run_main


def main():
    """Main entry point for the mortar strength extraction skill."""
    parser = argparse.ArgumentParser(
        description="Extract structured data from mortar strength inspection reports"
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='PDF or image files to process'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='data/output',
        help='Output directory (default: data/output)'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['json', 'csv', 'excel', 'all'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--model',
        '-m',
        choices=['claude', 'qwen'],
        help='Model to use for extraction (overrides env config)'
    )
    
    args = parser.parse_args()
    
    # Call the actual processing function and return proper exit code
    return_code = run_main(args)
    raise SystemExit(return_code)


if __name__ == '__main__':
    main()
