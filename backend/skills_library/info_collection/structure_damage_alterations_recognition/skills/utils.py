"""
Utility Functions for Structure Damage and Alterations Extraction
工具函数
"""

import re
import json
from typing import Any, Dict, Optional
from datetime import datetime




def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    # Remove leading ```lang and trailing ``` if present
    stripped = re.sub(r'^```[a-zA-Z0-9]*\s*', '', stripped)
    stripped = re.sub(r'\s*```$', '', stripped)
    return stripped.strip()


def _extract_json_block(text: str) -> str | None:
    if not text:
        return None
    candidate = _strip_code_fences(text)
    if not candidate:
        return None

    # Try object first
    start = candidate.find('{')
    end = candidate.rfind('}')
    if start != -1 and end != -1 and end > start:
        return candidate[start:end + 1]

    # Try array
    start = candidate.find('[')
    end = candidate.rfind(']')
    if start != -1 and end != -1 and end > start:
        return candidate[start:end + 1]

    return None

def clean_string(text: Optional[str]) -> Optional[str]:
    """
    清洗字符串:去首尾空格、压缩连续空格
    
    Args:
        text: 输入文本
        
    Returns:
        清洗后的文本
    """
    if not text or not isinstance(text, str):
        return None
    
    # 去首尾空格
    text = text.strip()
    
    # 压缩连续空格为1个
    text = re.sub(r'\s+', ' ', text)
    
    return text if text else None


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """
    规范化日期格式
    
    Args:
        date_str: 日期字符串
        
    Returns:
        规范化后的日期字符串(YYYY-MM-DD)或原字符串
    """
    if not date_str:
        return None
    
    date_str = clean_string(date_str)
    if not date_str:
        return None
    
    # 尝试多种日期格式
    date_patterns = [
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日?', '%Y-%m-%d'),
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', '%d-%m-%Y'),
    ]
    
    for pattern, date_format in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                if '年' in pattern:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                elif date_format == '%d-%m-%Y':
                    day, month, year = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except (ValueError, AttributeError):
                continue
    
    # 无法规范化则返回原字符串
    return date_str


def extract_dimension(text: Optional[str], dimension_type: str = 'length') -> Optional[str]:
    """
    从文本中提取尺寸信息
    
    Args:
        text: 输入文本
        dimension_type: 尺寸类型('length', 'width', 'height')
        
    Returns:
        提取的尺寸字符串
    """
    if not text:
        return None
    
    # 定义关键词
    keywords = {
        'length': ['长度', '长', 'L'],
        'width': ['宽度', '宽', 'W', '厚度', '厚'],
        'height': ['高度', '高', 'H']
    }
    
    # 尺寸模式: 数字+单位
    dimension_pattern = r'(\d+\.?\d*)\s*(mm|cm|m|米|毫米|厘米)'
    
    # 查找包含关键词的尺寸
    for keyword in keywords.get(dimension_type, []):
        pattern = f'{keyword}[约为是:：]?\s*{dimension_pattern}'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            unit = match.group(2)
            # 统一单位
            if unit in ['米', 'm']:
                unit = 'm'
            elif unit in ['厘米', 'cm']:
                unit = 'cm'
            elif unit in ['毫米', 'mm']:
                unit = 'mm'
            return f"{value}{unit}"
    
    return None


def validate_json_output(json_str: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    验证JSON输出格式
    
    Args:
        json_str: JSON字符串
        
    Returns:
        (是否有效, 解析后的字典, 错误信息)
    """
    try:
        if not json_str or not json_str.strip():
            return False, None, "Empty response"

        cleaned = _extract_json_block(json_str)
        if not cleaned:
            return False, None, "JSON block not found"

        data = json.loads(cleaned)

        # Required top-level fields
        if 'meta' not in data:
            return False, None, "Missing 'meta' field"

        # Accept items (preferred) or rows (legacy)
        if 'items' in data:
            if not isinstance(data['items'], list):
                return False, None, "'items' must be a list"
        elif 'rows' in data:
            if not isinstance(data['rows'], list):
                return False, None, "'rows' must be a list"
            data['items'] = data['rows']
            data.pop('rows', None)
        else:
            return False, None, "Missing 'items' field"

        return True, data, None

    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {str(e)}"
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"



def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    清洁提取的数据
    
    Args:
        data: 原始提取数据
        
    Returns:
        清洁后的数据
    """
    cleaned = {}
    
    # Clean meta
    if 'meta' in data:
        cleaned['meta'] = {}
        for key, value in data['meta'].items():
            if isinstance(value, str):
                if key == 'inspection_date':
                    cleaned['meta'][key] = normalize_date(value)
                else:
                    cleaned['meta'][key] = clean_string(value)
            else:
                cleaned['meta'][key] = value

    # Normalize rows -> items and clean items
    items = None
    if 'items' in data:
        items = data.get('items')
    elif 'rows' in data:
        items = data.get('rows')

    if items is not None:
        cleaned['items'] = []
        for row in items:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    cleaned_row[key] = clean_string(value)
                else:
                    cleaned_row[key] = value
            cleaned['items'].append(cleaned_row)

    # Preserve other fields
    for key in ['signoff', 'source_file', 'status', 'notes']:
        if key in data:
            cleaned[key] = data[key]

    return cleaned


def format_error_message(error: Exception, context: str = "") -> str:
    """
    格式化错误信息
    
    Args:
        error: 异常对象
        context: 上下文信息
        
    Returns:
        格式化后的错误信息
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"[{context}] {error_type}: {error_msg}"
    else:
        return f"{error_type}: {error_msg}"


def is_placeholder(value: Any) -> bool:
    """
    判断值是否为占位符
    
    Args:
        value: 待判断的值
        
    Returns:
        是否为占位符
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        value = value.strip()
        placeholders = ['—', '-', '/', '//', '', 'null', 'NULL', 'None', 'N/A', 'n/a']
        return value in placeholders
    
    return False


def safe_int(value: Any) -> Optional[int]:
    """
    安全转换为整数
    
    Args:
        value: 待转换的值
        
    Returns:
        整数或None
    """
    if is_placeholder(value):
        return None
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any, precision: int = 1) -> Optional[float]:
    """
    安全转换为浮点数
    
    Args:
        value: 待转换的值
        precision: 小数精度
        
    Returns:
        浮点数或None
    """
    if is_placeholder(value):
        return None
    
    try:
        return round(float(value), precision)
    except (ValueError, TypeError):
        return None
