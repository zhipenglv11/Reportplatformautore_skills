"""
Data Formatter for Output Generation
数据格式化输出模块
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
except ImportError:
    pd = None
    logging.warning("pandas not available, Excel/CSV export disabled")


logger = logging.getLogger(__name__)


class DataFormatter:
    """Formatter for extraction results."""
    
    @staticmethod
    def to_json(
        data: Dict[str, Any],
        output_path: Optional[str] = None,
        indent: int = 2
    ) -> str:
        """
        Format data as JSON.
        
        Args:
            data: Data to format
            output_path: Optional path to save JSON file
            indent: JSON indentation
            
        Returns:
            JSON string
        """
        json_str = json.dumps(data, ensure_ascii=False, indent=indent)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            logger.info(f"JSON saved to {output_path}")
        
        return json_str
    
    @staticmethod
    def to_csv(
        data: List[Dict[str, Any]],
        output_path: str,
        **kwargs
    ) -> None:
        """
        Format data as CSV.
        
        Args:
            data: List of data dictionaries
            output_path: Path to save CSV file
            **kwargs: Additional arguments for pandas.to_csv()
            
        Raises:
            ImportError: If pandas is not installed
        """
        if pd is None:
            raise ImportError("pandas is required for CSV export")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig', **kwargs)
        
        logger.info(f"CSV saved to {output_path}")
    
    @staticmethod
    def to_excel(
        data: List[Dict[str, Any]],
        output_path: str,
        sheet_name: str = 'Sheet1',
        **kwargs
    ) -> None:
        """
        Format data as Excel.
        
        Args:
            data: List of data dictionaries
            output_path: Path to save Excel file
            sheet_name: Name of the worksheet
            **kwargs: Additional arguments for pandas.to_excel()
            
        Raises:
            ImportError: If pandas or openpyxl is not installed
        """
        if pd is None:
            raise ImportError("pandas is required for Excel export")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False, sheet_name=sheet_name, **kwargs)
        
        logger.info(f"Excel saved to {output_path}")
    
    @staticmethod
    def format_batch_results(
        results: List[Dict[str, Any]],
        output_dir: str,
        formats: List[str] = ['json'],
        base_name: str = 'mortar_extraction'
    ) -> Dict[str, str]:
        """
        Format and save batch processing results in multiple formats.
        
        Args:
            results: List of extraction results
            output_dir: Output directory
            formats: List of formats to generate ('json', 'csv', 'excel')
            base_name: Base name for output files
            
        Returns:
            Dictionary mapping format to output file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        # JSON (full results)
        if 'json' in formats:
            json_path = output_dir / f'{base_name}_results.json'
            DataFormatter.to_json(
                {'results': results, 'total': len(results)},
                str(json_path)
            )
            output_files['json'] = str(json_path)
        
        # CSV (flattened data)
        if 'csv' in formats:
            csv_path = output_dir / f'{base_name}_results.csv'
            try:
                DataFormatter.to_csv(results, str(csv_path))
                output_files['csv'] = str(csv_path)
            except Exception as e:
                logger.warning(f"Failed to generate CSV: {e}")
        
        # Excel
        if 'excel' in formats:
            excel_path = output_dir / f'{base_name}_results.xlsx'
            try:
                DataFormatter.to_excel(results, str(excel_path))
                output_files['excel'] = str(excel_path)
            except Exception as e:
                logger.warning(f"Failed to generate Excel: {e}")
        
        return output_files
    
    @staticmethod
    def generate_report(
        results: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """
        Generate a summary report of extraction results.
        
        Args:
            results: List of extraction results
            output_path: Path to save report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        total = len(results)
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = total - successful
        
        report = {
            'summary': {
                'total_files': total,
                'successful': successful,
                'failed': failed,
                'success_rate': f"{successful/total*100:.2f}%" if total > 0 else "0%"
            },
            'details': results
        }
        
        DataFormatter.to_json(report, str(output_path))
        logger.info(f"Report generated: {output_path}")
