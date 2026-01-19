"""
配置管理模块
集中管理路径、常量和配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 路径配置
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API配置
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-vl-plus")

# 输出格式配置
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "json").lower()

# 支持的表格类型
TABLE_TYPES = {
    "混凝土回弹检测记录表": {
        "code": "concrete_strength_sheet",
        "name": "混凝土回弹检测记录表（结构物检测原始记录）",
        "description": "结构混凝土强度回弹检测，施工记录回溯、AI解析报告生成",
        "control_number": "KJQR-056-215",
        "keywords": ["KJQR-056-215", "构件检测", "现场结构检测", "回弹法", "构件检测原始记录", "结构检测"],
        "fields": ["检测部位", "混凝土品种", "检测方法", "强度等级", "施工日期"]
    },
    "混凝土强度检测表格": {
        "code": "concrete_strength_grid",
        "name": "回弹法检测混凝土强度原始记录（KSQR-4.13-XC-10）",
        "description": "用于结构实体混凝土强度回弹检测的原始数据采集",
        "control_number": "KSQR-4.13-XC-10",
        "keywords": ["KSQR-4.13-XC-10", "推定值", "平均值", "标准差", "JGJ/T 23-2011"],
        "fields": ["控制标号", "设计强度等级", "检测部位", "混凝土品种", "检测日期", "施工日期", "碳化深度", "测区强度最小值", "测区强度平均值", "测区强度标准差", "混凝土强度推定值"]
    }
}

# 文件类型支持
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
SUPPORTED_PDF_FORMATS = [".pdf"]
SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS + SUPPORTED_PDF_FORMATS
