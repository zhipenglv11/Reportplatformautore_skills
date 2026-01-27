"""
Output Formatter
输出格式化模块
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from skills.schema import StructureAlterationSchema


class Formatter:
    """输出格式化器"""

    @staticmethod
    def to_json(schema: StructureAlterationSchema, output_path: str,
                indent: int = 2) -> None:
        """
        导出为JSON格式
        
        Args:
            schema: 数据schema
            output_path: 输出路径
            indent: 缩进空格数
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema.to_dict(), f, ensure_ascii=False, indent=indent)

    @staticmethod
    def to_csv(schemas: List[StructureAlterationSchema], output_path: str) -> None:
        """
        导出为CSV格式
        
        Args:
            schemas: 数据schema列表
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 展开所有项数据
        rows_data = []
        for schema in schemas:
            meta = schema.meta
            signoff = schema.signoff
            for item in schema.items:
                row_dict = {
                    # Meta fields
                    '控制编号': meta.control_id,
                    '原始记录编号': meta.record_no,
                    '仪器编号': meta.instrument_id,
                    '检测日期': meta.test_date,
                    '房屋名称': meta.house_name,
                    # Item fields
                    '拆改部位': item.modification_location,
                    '拆改内容描述': item.modification_description,
                    '照片编号': item.photo_no,
                    # Signoff fields
                    '检查人': signoff.inspector,
                    '记录人': signoff.recorder,
                    '审核人': signoff.reviewer,
                    # Source
                    '源文件': schema.source_file
                }
                rows_data.append(row_dict)

        # 写入CSV
        if rows_data:
            df = pd.DataFrame(rows_data)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')

    @staticmethod
    def to_excel(schemas: List[StructureAlterationSchema], output_path: str) -> None:
        """
        导出为Excel格式
        
        Args:
            schemas: 数据schema列表
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 展开所有项数据
        rows_data = []
        for schema in schemas:
            meta = schema.meta
            signoff = schema.signoff
            for item in schema.items:
                row_dict = {
                    # Meta fields
                    '控制编号': meta.control_id,
                    '原始记录编号': meta.record_no,
                    '仪器编号': meta.instrument_id,
                    '检测日期': meta.test_date,
                    '房屋名称': meta.house_name,
                    # Item fields
                    '拆改部位': item.modification_location,
                    '拆改内容描述': item.modification_description,
                    '照片编号': item.photo_no,
                    # Signoff fields
                    '检查人': signoff.inspector,
                    '记录人': signoff.recorder,
                    '审核人': signoff.reviewer,
                    # Source
                    '源文件': schema.source_file
                }
                rows_data.append(row_dict)

        # 写入Excel
        if rows_data:
            df = pd.DataFrame(rows_data)
            df.to_excel(output_path, index=False, engine='openpyxl')

    @staticmethod
    def to_markdown(schema: StructureAlterationSchema, output_path: str) -> None:
        """
        导出为Markdown格式
        
        Args:
            schema: 数据schema
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        lines.append("# 结构损伤及拆改检查记录\n")

        # Meta信息
        lines.append("## 表头信息\n")
        meta = schema.meta
        lines.append(f"- **控制编号**: {meta.control_id or 'N/A'}")
        lines.append(f"- **原始记录编号**: {meta.record_no or 'N/A'}")
        lines.append(f"- **仪器编号**: {meta.instrument_id or 'N/A'}")
        lines.append(f"- **检测日期**: {meta.test_date or 'N/A'}")
        lines.append(f"- **房屋名称**: {meta.house_name or 'N/A'}\n")

        # 表格数据
        lines.append("## 检查记录\n")
        if schema.items:
            # 表头
            lines.append("| 拆改部位 | 拆改内容描述 | 照片编号 |")
            lines.append("|----------|--------------|----------|")

            # 数据行
            for item in schema.items:
                lines.append(
                    f"| {item.modification_location or ''} "
                    f"| {item.modification_description or ''} "
                    f"| {item.photo_no or ''} |"
                )
        else:
            lines.append("*无数据*")

        # 签名信息
        lines.append("\n## 签名信息\n")
        signoff = schema.signoff
        lines.append(f"- **检查人**: {signoff.inspector or 'N/A'}")
        lines.append(f"- **记录人**: {signoff.recorder or 'N/A'}")
        lines.append(f"- **审核人**: {signoff.reviewer or 'N/A'}")

        # 源文件
        lines.append(f"\n---\n*源文件: {schema.source_file}*")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    @staticmethod
    def format_all(schemas: List[StructureAlterationSchema],
                  output_dir: str, base_name: str = 'output') -> Dict[str, str]:
        """
        导出所有格式
        
        Args:
            schemas: 数据schema列表
            output_dir: 输出目录
            base_name: 基础文件名
            
        Returns:
            格式->文件路径的映射
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_files = {}

        # JSON (每个schema一个文件)
        for i, schema in enumerate(schemas):
            json_path = output_dir / f"{base_name}_{i+1}.json"
            Formatter.to_json(schema, str(json_path))
            output_files[f'json_{i+1}'] = str(json_path)

        # CSV (合并所有)
        csv_path = output_dir / f"{base_name}.csv"
        Formatter.to_csv(schemas, str(csv_path))
        output_files['csv'] = str(csv_path)

        # Excel (合并所有)
        excel_path = output_dir / f"{base_name}.xlsx"
        Formatter.to_excel(schemas, str(excel_path))
        output_files['excel'] = str(excel_path)

        # Markdown (每个schema一个文件)
        for i, schema in enumerate(schemas):
            md_path = output_dir / f"{base_name}_{i+1}.md"
            Formatter.to_markdown(schema, str(md_path))
            output_files[f'markdown_{i+1}'] = str(md_path)

        return output_files
