"""
Utility functions for Delegate Info Check
"""

import re
import json
from typing import Any, Dict, Optional


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    stripped = re.sub(r'^```[a-zA-Z0-9]*\s*', '', stripped)
    stripped = re.sub(r'\s*```$', '', stripped)
    return stripped.strip()


def _extract_json_block(text: str) -> Optional[str]:
    if not text:
        return None
    candidate = _strip_code_fences(text)
    if not candidate:
        return None
    start = candidate.find('{')
    end = candidate.rfind('}')
    if start != -1 and end != -1 and end > start:
        return candidate[start:end + 1]
    return None


def clean_string(text: Optional[str]) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text if text else None


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    date_str = clean_string(date_str)
    if not date_str:
        return None
    m = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', date_str)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return date_str


def validate_json_output(json_str: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    try:
        if not json_str or not json_str.strip():
            return False, None, "Empty response"
        cleaned = _extract_json_block(json_str)
        if not cleaned:
            return False, None, "JSON block not found"
        data = json.loads(cleaned)
        if 'meta' not in data:
            return False, None, "Missing 'meta' field"
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"JSON decode error: {str(e)}"
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"


def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
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

    if 'house_details' in data:
        if isinstance(data['house_details'], list):
            cleaned['house_details'] = [clean_string(v) for v in data['house_details']]
        else:
            cleaned['house_details'] = clean_string(data['house_details'])

    for key in ['source_file', 'status', 'notes']:
        if key in data:
            cleaned[key] = data[key]
    return cleaned
