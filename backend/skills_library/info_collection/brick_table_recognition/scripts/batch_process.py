#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch process brick strength (rebound method) tables.
"""

import sys
import io
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 保存原始的 excepthook，防止某些库（如 openai）修改后在 subprocess 环境中出错
_original_excepthook = sys.excepthook

from scripts.config import TABLE_TYPES, OUTPUT_DIR
from scripts.pdf_processor import process_file
from scripts.qwen_client import (
    classify_table_type,
    extract_table_data,
    test_api_connection,
)
from scripts.formatter import format_output

# 在导入可能修改 excepthook 的库后，创建一个健壮的 excepthook
def robust_excepthook(exc_type, exc_value, exc_traceback):
    """健壮的异常钩子，即使在 stdout/stderr 有问题时也能工作"""
    try:
        # 尝试使用原始的 excepthook
        _original_excepthook(exc_type, exc_value, exc_traceback)
    except:
        # 如果失败，尝试直接写入 stderr
        try:
            import traceback
            sys.stderr.write(f"{exc_type.__name__}: {exc_value}\n")
            traceback.print_tb(exc_traceback, file=sys.stderr)
        except:
            # 最后的尝试：写入文件
            try:
                with open("error.log", "w", encoding="utf-8") as f:
                    f.write(f"{exc_type.__name__}: {exc_value}\n")
                    import traceback
                    traceback.print_tb(exc_traceback, file=f)
            except:
                pass

# 应用健壮的 excepthook
sys.excepthook = robust_excepthook


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass


def load_table_schema(table_type_name: str) -> Dict[str, Any]:
    if "砖强度（回弹法）原始记录表" in table_type_name or "brick_strength_rebound_raw" in table_type_name:
        return {
            "type": "object",
            "properties": {
                "table_id": {"type": ["string", "null"]},
                "commission_id": {"type": ["string", "null"]},
                "test_date": {"type": ["string", "null"]},
                "instrument_id": {"type": ["string", "null"]},
                "brick_type": {"type": ["string", "null"]},
                "strength_grade": {"type": ["string", "null"]},
                "rows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test_location": {"type": ["string", "null"]},
                            "estimated_strength_mpa": {"type": ["number", "null"]},
                        },
                        "required": [
                            "test_location",
                            "estimated_strength_mpa",
                        ],
                    },
                },
            },
            "required": [
                "table_id",
                "commission_id",
                "test_date",
                "instrument_id",
                "brick_type",
                "strength_grade",
                "rows",
            ],
        }

    return {"type": "object", "properties": {"table_type": {"type": "string"}}}


def process_single_file(file_path: Path, output_dir: Path) -> Dict[str, Any]:
    result = {
        "file": str(file_path),
        "success": False,
        "type": None,
        "data": None,
        "error": None,
    }

    try:
        safe_print(f"\n📄 Processing: {file_path.name}")
        image_paths = process_file(file_path)
        safe_print(f"   Generated {len(image_paths)} image(s)")

        all_data = []
        for i, image_path in enumerate(image_paths):
            safe_print(f"\n🧾 Image {i + 1}/{len(image_paths)}: {image_path.name}")

            safe_print("   Classifying table type...")
            classification = classify_table_type(image_path)
            if not classification["success"]:
                result["error"] = f"分类失败: {classification.get('error', '未知错误')}"
                return result

            table_type = classification["type"]
            result["type"] = table_type
            safe_print(f"   ✅ Type: {table_type}")

            safe_print("   Extracting table data...")
            schema = load_table_schema(table_type)
            extraction = extract_table_data(image_path, table_type, schema)

            if not extraction["success"]:
                result["error"] = f"提取失败: {extraction.get('error', '未知错误')}"
                return result

            extracted_data = extraction["data"]
            extracted_data["file"] = file_path.name
            extracted_data["image_index"] = i + 1
            all_data.append(extracted_data)
            safe_print("   ✅ Extraction complete")

        result["data"] = all_data
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        safe_print(f"   ❌ Failed: {e}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Batch process brick strength tables")
    parser.add_argument("files", nargs="*", help="Input file paths (PDF or images)")
    parser.add_argument("--output-dir", "-o", type=str, help="Output directory", default=None)
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "excel"],
        help="Output format",
        default=None,
    )
    parser.add_argument("--test-api", action="store_true", help="Test API connection")

    args = parser.parse_args()

    if args.test_api:
        test_api_connection()
        return

    if not args.files:
        parser.error("Please provide at least one file path, or use --test-api")

    from scripts.config import QWEN_API_KEY

    if not QWEN_API_KEY:
        safe_print("❌ Missing QWEN_API_KEY in .env")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    for file_path_str in args.files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            safe_print(f"⚠️  File not found, skipped: {file_path}")
            continue

        result = process_single_file(file_path, output_dir)
        all_results.append(result)

    successful_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]

    safe_print("\n" + "=" * 60)
    safe_print("📊 Done:")
    safe_print(f"   ✅ Success: {len(successful_results)}/{len(all_results)}")
    safe_print(f"   ❌ Failed: {len(failed_results)}/{len(all_results)}")

    if successful_results:
        all_data = []
        for result in successful_results:
            all_data.extend(result["data"])

        output_file = format_output(all_data, "brick_tables", args.format)
        safe_print(f"\n📦 Saved output to: {output_file}")

    report_file = output_dir / "processing_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    safe_print(f"🧾 Report saved to: {report_file}")

    if failed_results:
        safe_print("\n❌ Failed files:")
        for result in failed_results:
            safe_print(f"   {result['file']}: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
