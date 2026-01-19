#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理表格文件
主入口脚本
"""

import sys
import io

# Windows控制台编码修复
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

from scripts.config import TABLE_TYPES, OUTPUT_DIR
from scripts.pdf_processor import process_file, is_pdf_file
from scripts.qwen_client import (
    classify_table_type,
    extract_table_data,
    test_api_connection,
)
from scripts.formatter import format_output


def safe_print(*args, **kwargs):
    """安全打印，处理I/O错误"""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        pass


def load_table_schema(table_type_name: str) -> Dict[str, Any]:
    """
    加载表格类型的JSON Schema

    Args:
        table_type_name: 表格类型名称（如："混凝土回弹检测记录表"）

    Returns:
        表格类型的JSON Schema字典
    """
    # 混凝土回弹检测记录表的Schema
    if (
        "混凝土回弹检测记录表" in table_type_name
        or "concrete_strength_sheet" in table_type_name
    ):
        return {
            "type": "object",
            "properties": {
                "检测日期": {
                    "type": "string",
                    "description": "表格右上角「检测日期」字段，格式如：2024-10-10",
                },
                "检测原因": {
                    "type": "string",
                    "description": "表格中部靠右的「检测原因」字段，如：委托检测",
                },
                "检测方法": {
                    "type": "string",
                    "description": "表格中部靠右的「检测方法」字段，如：回弹法",
                },
                "检测部位": {
                    "type": "string",
                    "description": "从「工程名称」或「检测部位」字段提取，如：2#楼柱梁板楼面",
                },
                "混凝土品种": {
                    "type": "string",
                    "description": "表格右上方的「混凝土品种」字段，如：泵送混凝土",
                },
                "强度等级": {
                    "type": "string",
                    "description": "表格右下区域每行「强度等级」字段，统一提取为主等级，如：C30",
                },
                "施工日期列表": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": '所有明细行中的「施工日期」去重后组成的数组，如：["2021"]',
                },
            },
            "required": [
                "检测日期",
                "检测原因",
                "检测方法",
                "检测部位",
                "混凝土品种",
                "强度等级",
                "施工日期列表",
            ],
        }

    # 混凝土强度检测表格的Schema（KSQR-4.13-XC-10）
    elif (
        "混凝土强度检测表格" in table_type_name
        or "concrete_strength_grid" in table_type_name
    ):
        return {
            "type": "object",
            "properties": {
                "控制标号": {
                    "type": "string",
                    "description": "表格左上角控制编号，如：KSQR-4.13-XC-10",
                },
                "设计强度等级": {
                    "type": "string",
                    "description": "混凝土设计强度等级，如：C30",
                },
                "检测部位": {
                    "type": "string",
                    "description": "混凝土构件位置描述，如：一层柱3/1/B",
                },
                "混凝土品种": {
                    "type": "string",
                    "description": "混凝土类型，如：泵送混凝土",
                },
                "检测日期": {
                    "type": "string",
                    "description": "表格右上区域，如：2024-10-14",
                },
                "施工日期": {
                    "type": "string",
                    "description": "表格右上区域，如：2021-01-01",
                },
                "碳化深度（mm）": {
                    "type": "number",
                    "description": "表格中「碳化深度」列的「计算」值，数值类型，如：6.00",
                },
                "测区强度最小值（MPa）": {
                    "type": "number",
                    "description": "表格底部字段，数值类型，如：33.7",
                },
                "测区强度平均值（MPa）": {
                    "type": "number",
                    "description": "表格底部字段，数值类型，如：35.7",
                },
                "测区强度标准差（MPa）": {
                    "type": "number",
                    "description": "表格底部字段，数值类型，如：1.19",
                },
                "混凝土强度推定值（MPa）": {
                    "type": "number",
                    "description": "最终计算结果，数值类型，如：33.7",
                },
            },
            "required": [
                "控制标号",
                "设计强度等级",
                "检测部位",
                "混凝土品种",
                "检测日期",
                "施工日期",
                "碳化深度（mm）",
                "测区强度最小值（MPa）",
                "测区强度平均值（MPa）",
                "测区强度标准差（MPa）",
                "混凝土强度推定值（MPa）",
            ],
        }

    # 默认返回基本结构（用于其他未定义的表格类型）
    return {
        "type": "object",
        "properties": {"表格类型": {"type": "string"}, "数据": {"type": "array"}},
    }


def process_single_file(file_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    处理单个文件

    Args:
        file_path: 输入文件路径
        output_dir: 输出目录

    Returns:
        处理结果字典
    """
    result = {
        "file": str(file_path),
        "success": False,
        "type": None,
        "data": None,
        "error": None,
    }

    try:
        # 1. 转换文件为图片（如果是PDF）
        safe_print(f"\n📄 处理文件: {file_path.name}")
        image_paths = process_file(file_path)
        safe_print(f"   生成 {len(image_paths)} 张图片")

        # 2. 对每张图片进行分类和提取（通常只有第一页）
        all_data = []
        for i, image_path in enumerate(image_paths):
            safe_print(f"\n🖼️  处理图片 {i + 1}/{len(image_paths)}: {image_path.name}")

            # 分类表格类型
            safe_print("   分类表格类型...")
            classification = classify_table_type(image_path)
            if not classification["success"]:
                result["error"] = f"分类失败: {classification.get('error', '未知错误')}"
                return result

            table_type = classification["type"]
            result["type"] = table_type
            safe_print(f"   ✅ 识别类型: {table_type}")

            # 提取表格数据
            safe_print("   提取表格数据...")
            schema = load_table_schema(table_type)
            extraction = extract_table_data(image_path, table_type, schema)

            if not extraction["success"]:
                result["error"] = f"提取失败: {extraction.get('error', '未知错误')}"
                return result

            extracted_data = extraction["data"]
            extracted_data["文件"] = file_path.name
            extracted_data["图片序号"] = i + 1
            all_data.append(extracted_data)
            safe_print(f"   ✅ 数据提取完成")

        result["data"] = all_data
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        safe_print(f"   ❌ 处理失败: {e}")

    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量处理混凝土表格文件")
    parser.add_argument("files", nargs="*", help="要处理的文件路径（支持PDF和图片）")
    parser.add_argument("--output-dir", "-o", type=str, help="输出目录", default=None)
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "excel"],
        help="输出格式",
        default=None,
    )
    parser.add_argument("--test-api", action="store_true", help="测试API连接")

    args = parser.parse_args()

    # 测试API连接
    if args.test_api:
        test_api_connection()
        return
    
    # 如果没有提供文件且不是测试API，报错
    if not args.files:
        parser.error("需要提供至少一个文件路径，或使用 --test-api 测试API连接")

    # 检查API配置
    from scripts.config import QWEN_API_KEY

    if not QWEN_API_KEY:
        safe_print("❌ 错误: 未配置QWEN_API_KEY")
        safe_print("   请在.env文件中设置QWEN_API_KEY=your_api_key")
        sys.exit(1)

    # 设置输出目录
    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理文件
    all_results = []
    for file_path_str in args.files:
        file_path = Path(file_path_str)
        if not file_path.exists():
            safe_print(f"⚠️  文件不存在，跳过: {file_path}")
            continue

        result = process_single_file(file_path, output_dir)
        all_results.append(result)

    # 汇总结果
    successful_results = [r for r in all_results if r["success"]]
    failed_results = [r for r in all_results if not r["success"]]

    safe_print("\n" + "=" * 60)
    safe_print(f"📊 处理完成:")
    safe_print(f"   ✅ 成功: {len(successful_results)}/{len(all_results)}")
    safe_print(f"   ❌ 失败: {len(failed_results)}/{len(all_results)}")

    # 保存结果
    if successful_results:
        # 合并所有成功的数据
        all_data = []
        for result in successful_results:
            all_data.extend(result["data"])

        # 格式化输出
        output_file = format_output(all_data, "concrete_tables", args.format)
        safe_print(f"\n💾 结果已保存到: {output_file}")

    # 保存详细报告
    report_file = output_dir / "processing_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    safe_print(f"📋 详细报告已保存到: {report_file}")

    # 如果有失败的，显示错误信息
    if failed_results:
        safe_print("\n❌ 失败的文件:")
        for result in failed_results:
            safe_print(f"   {result['file']}: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()
