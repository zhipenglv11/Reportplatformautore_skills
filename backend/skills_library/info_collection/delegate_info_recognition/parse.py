#!/usr/bin/env python3
"""
Delegate Info Check - Main Entry Point
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.run import main as run_main


def main():
    parser = argparse.ArgumentParser(
        description="Extract delegate info check fields from PDF/images"
    )
    parser.add_argument('files', nargs='+', help='PDF or image files to process')
    parser.add_argument('--output', '-o', default='data/output', help='Output directory')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'excel', 'all'], default='json')
    parser.add_argument('--model', '-m', choices=['claude', 'qwen'])

    args = parser.parse_args()
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"Error: file not found {file_path}")
            sys.exit(1)

    return_code = run_main(args)
    raise SystemExit(return_code)


if __name__ == '__main__':
    main()
