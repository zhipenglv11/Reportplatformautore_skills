"""
Output formatter for delegate info check.
"""

from pathlib import Path
from typing import Any, Dict, List
import json

try:
    import pandas as pd
except Exception:
    pd = None


class Formatter:
    @staticmethod
    def to_json(data: Any, output_path: str, indent: int = 2) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    @staticmethod
    def to_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
        if pd is None:
            raise ImportError("pandas is required for CSV export")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

    @staticmethod
    def to_excel(rows: List[Dict[str, Any]], output_path: str) -> None:
        if pd is None:
            raise ImportError("pandas is required for Excel export")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        df.to_excel(output_path, index=False, engine="openpyxl")

    @staticmethod
    def format_all(rows: List[Dict[str, Any]], output_dir: str, base_name: str = "output") -> Dict[str, str]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_files: Dict[str, str] = {}

        json_path = output_dir / f"{base_name}.json"
        Formatter.to_json(rows, str(json_path))
        output_files["json"] = str(json_path)

        if pd is not None:
            csv_path = output_dir / f"{base_name}.csv"
            Formatter.to_csv(rows, str(csv_path))
            output_files["csv"] = str(csv_path)

            excel_path = output_dir / f"{base_name}.xlsx"
            Formatter.to_excel(rows, str(excel_path))
            output_files["excel"] = str(excel_path)

        return output_files
