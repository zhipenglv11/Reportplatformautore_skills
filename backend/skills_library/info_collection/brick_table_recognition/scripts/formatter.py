"""
数据格式化模块
将提取的数据格式化为不同输出格式
"""

import json
import csv
import sys
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from openpyxl import Workbook

from scripts.config import OUTPUT_FORMAT, OUTPUT_DIR


def format_as_json(data: List[Dict[str, Any]], output_path: Path) -> Path:
    """格式化为JSON"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_path


def format_as_csv(data: List[Dict[str, Any]], output_path: Path) -> Path:
    """格式化为CSV"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # 创建空CSV文件
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            f.write("")
        return output_path

    # 使用pandas处理（自动处理嵌套结构）
    df = pd.json_normalize(data)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def format_as_excel(data: List[Dict[str, Any]], output_path: Path) -> Path:
    """格式化为Excel"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # 创建空Excel文件
        wb = Workbook()
        wb.save(output_path)
        return output_path

    # 使用pandas处理
    df = pd.json_normalize(data)
    df.to_excel(output_path, index=False, engine="openpyxl")
    return output_path


def format_output(
    data: List[Dict[str, Any]], filename: str, format_type: Optional[str] = None
) -> Path:
    """
    格式化输出数据

    Args:
        data: 要输出的数据列表
        filename: 输出文件名（不含扩展名）
        format_type: 输出格式（json/csv/excel），默认使用配置中的格式

    Returns:
        输出文件路径
    """
    if format_type is None:
        format_type = OUTPUT_FORMAT

    output_path = OUTPUT_DIR / f"{filename}.{format_type}"

    if format_type == "json":
        return format_as_json(data, output_path)
    elif format_type == "csv":
        return format_as_csv(data, output_path)
    elif format_type == "excel" or format_type == "xlsx":
        return format_as_excel(data, output_path)
    else:
        raise ValueError(f"不支持的输出格式: {format_type}")


if __name__ == "__main__":
    # 测试
    test_data = [{"name": "测试1", "value": 100}, {"name": "测试2", "value": 200}]
    output_file = format_output(test_data, "test_output", "json")
    print(f"✅ 测试输出已保存到: {output_file}")
