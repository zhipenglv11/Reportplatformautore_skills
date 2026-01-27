"""
Utility Functions for Mortar Strength Extraction
砂浆强度检测数据抽取工具函数
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple


logger = logging.getLogger(__name__)


def clean_json_response(response: str) -> str:
    """
    Clean LLM response to extract valid JSON.
    
    Args:
        response: Raw response from LLM
        
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*$', '', response)
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    # Try to extract JSON if surrounded by text
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        response = json_match.group(0)
    
    return response


def validate_extraction(
    extracted_data: Dict[str, Any],
    schema_class: type
) -> Dict[str, Any]:
    """
    Validate extracted data against schema.
    
    Args:
        extracted_data: Extracted data dictionary
        schema_class: Schema class to validate against
        
    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'errors': List[str],
            'warnings': List[str]
        }
    """
    errors = []
    warnings = []
    
    # Get schema information
    all_fields = schema_class.get_field_names()
    required_fields = schema_class.get_required_fields()
    
    # Check required fields
    for field in required_fields:
        if field not in extracted_data or extracted_data[field] is None:
            errors.append(f"Required field missing: {field}")
    
    # Check for unexpected fields
    for field in extracted_data.keys():
        if field not in all_fields:
            warnings.append(f"Unexpected field found: {field}")
    
    # Type validation (TODO: implement specific type checks)
    # 等用户提供字段后,可以添加更具体的类型和范围验证
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def normalize_field_value(field_name: str, value: Any) -> Any:
    """
    Normalize field value according to field type.
    
    Args:
        field_name: Name of the field
        value: Raw value to normalize
        
    Returns:
        Normalized value
    """
    if value is None:
        return None
    
    # String fields - light cleaning
    if field_name in ['table_id', 'record_no', 'instrument_model', 'test_location']:
        value_str = str(value).strip()
        # Compress multiple spaces to single space
        value_str = ' '.join(value_str.split())
        return value_str if value_str else None
    
    # Date field
    if field_name == 'test_date':
        return format_date(str(value))
    
    # Number fields (MPa values)
    if field_name in ['converted_strength_mpa', 'estimated_strength_mpa']:
        # Check for placeholder values
        value_str = str(value).strip()
        if value_str in ['', '—', '//', '/', '-', 'null']:
            return None
        
        numeric = extract_numeric_value(value_str)
        if numeric is not None:
            # 保留原始数值位数，不进行四舍五入
            return numeric
        return None
    
    # Integer field (seq)
    if field_name == 'seq':
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    return value


def format_date(date_str: str) -> Optional[str]:
    """
    Format date string to standard format (YYYY-MM-DD).
    
    Args:
        date_str: Raw date string
        
    Returns:
        Formatted date string or None if invalid
    """
    if not date_str:
        return None
    
    # Try common date formats
    date_patterns = [
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM-DD-YYYY or DD-MM-YYYY
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',      # Chinese format
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, str(date_str))
        if match:
            groups = match.groups()
            # TODO: Add more sophisticated date parsing
            return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
    
    return None


def extract_numeric_value(text: str) -> Optional[float]:
    """
    Extract numeric value from text.
    
    Args:
        text: Text containing numeric value
        
    Returns:
        Extracted numeric value or None
    """
    if not text:
        return None
    
    # Remove common units and non-numeric characters
    text = str(text).strip()
    text = re.sub(r'[^0-9.-]', '', text)
    
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def merge_extraction_results(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge multiple extraction results (for multi-page documents).
    
    Args:
        results: List of extraction results
        
    Returns:
        Merged result dictionary
    """
    if not results:
        return {}
    
    if len(results) == 1:
        return results[0]
    
    # TODO: Implement merging logic based on actual field structure
    # 目前返回第一个结果,用户提供字段后可以实现更智能的合并
    
    merged = results[0].copy()
    merged['_merged_from_pages'] = len(results)
    
    return merged


def calculate_confidence_score(
    extracted_data: Dict[str, Any],
    validation_result: Dict[str, Any]
) -> float:
    """
    Calculate confidence score for extraction result.
    
    Args:
        extracted_data: Extracted data
        validation_result: Validation result
        
    Returns:
        Confidence score between 0 and 1
    """
    score = 1.0
    
    # Penalize for errors
    if validation_result['errors']:
        score -= 0.1 * len(validation_result['errors'])
    
    # Penalize for warnings
    if validation_result['warnings']:
        score -= 0.05 * len(validation_result['warnings'])
    
    # Penalize for missing fields
    total_fields = len(extracted_data)
    null_fields = sum(1 for v in extracted_data.values() if v is None)
    if total_fields > 0:
        completeness = 1 - (null_fields / total_fields)
        score *= completeness
    
    return max(0.0, min(1.0, score))
