# -*- coding: utf-8 -*-
"""
测试 PDF 转图片功能（已改用 PyMuPDF，无需 Poppler）
运行方式: 在 backend 目录下执行 python test_poppler_config.py
"""

from pathlib import Path
import sys

# Test 1: Config (poppler_bin_path 已弃用，仅作兼容)
print("=" * 80)
print("测试1: 主配置文件 (backend/config.py)")
print("=" * 80)

from config import settings

print(f"poppler_bin_path (已弃用): {settings.poppler_bin_path or '(空)'}")

# Test 2: PyMuPDF 与统一 PDF 转图片接口
print("\n" + "=" * 80)
print("测试2: PyMuPDF / services.tools.pdf_to_image")
print("=" * 80)

try:
    from services.tools.pdf_to_image import pdf_to_images
    print("✓ services.tools.pdf_to_image 可导入")

    try:
        import fitz
        print("✓ PyMuPDF (fitz) 已安装")
    except ImportError:
        print("✗ PyMuPDF 未安装，请执行: pip install pymupdf")
        sys.exit(1)
except Exception as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("所有测试通过（PDF 转图片已使用 PyMuPDF，无需 Poppler）")
print("=" * 80)
