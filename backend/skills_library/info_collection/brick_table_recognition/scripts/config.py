"""
Config for brick table recognition pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API config (kept same as concrete)
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-vl-plus")

# Output format
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "json").lower()

# Supported table types
TABLE_TYPES = {
    "砖强度（回弹法）原始记录表": {
        "code": "brick_strength_rebound_raw",
        "name": "砖强度（回弹法）原始记录表",
        "description": "用于砖强度回弹法检测的原始记录表，抽取表头与行级检测数据",
        "control_number": "KJQR-056-223",
        "keywords": [
            "KJQR-056-223",
            "砖强度",
            "回弹法",
            "原始记录表",
            "检测日期",
            "仪器编号",
            "砖的种类",
            "强度等级",
            "强度推定值",
        ],
        "fields": [
            "table_id",
            "test_date",
            "instrument_id",
            "brick_type",
            "strength_grade",
            "rows[].seq",
            "rows[].test_location",
            "rows[].estimated_strength_mpa",
        ],
    }
}

# File types
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
SUPPORTED_PDF_FORMATS = [".pdf"]
SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS + SUPPORTED_PDF_FORMATS
