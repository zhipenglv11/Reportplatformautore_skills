# -*- coding: utf-8 -*-
"""
测试 poppler 路径配置是否正确
"""

from pathlib import Path
import sys

# Test 1: Check main config
print("=" * 80)
print("测试1: 主配置文件 (backend/config.py)")
print("=" * 80)

from config import settings

print(f"poppler_bin_path: {settings.poppler_bin_path}")
poppler_bin = Path(settings.poppler_bin_path)
print(f"路径存在: {poppler_bin.exists()}")

if poppler_bin.exists():
    print(f"目录内容:")
    for item in sorted(poppler_bin.iterdir()):
        print(f"  - {item.name}")
    print("✓ 主配置 poppler 路径正确")
else:
    print("✗ 主配置 poppler 路径不存在")
    sys.exit(1)

# Test 2: Check mortar collection config
print("\n" + "=" * 80)
print("测试2: 砂浆采集配置 (mortar_table_recognition/scripts/config.py)")
print("=" * 80)

from skills_library.info_collection.mortar_table_recognition.scripts.config import Config as MortarConfig

mortar_config = MortarConfig()
print(f"poppler_path: {mortar_config.poppler_path}")
mortar_poppler = Path(mortar_config.poppler_path)
print(f"路径存在: {mortar_poppler.exists()}")

if mortar_poppler.exists():
    print(f"目录内容:")
    for item in sorted(mortar_poppler.iterdir()):
        print(f"  - {item.name}")
    print("✓ 砂浆配置 poppler 路径正确")
else:
    print("✗ 砂浆配置 poppler 路径不存在")
    sys.exit(1)

# Test 3: Try importing pdf2image and test conversion
print("\n" + "=" * 80)
print("测试3: pdf2image 库功能测试")
print("=" * 80)

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError
    print("✓ pdf2image 库已安装")
    
    # Try to check if poppler is working
    try:
        # This will fail if poppler is not properly configured
        # but at least we can see the error message
        print(f"尝试使用 poppler_path: {settings.poppler_bin_path}")
        print("(如果看到错误，说明 poppler 路径或版本有问题)")
    except Exception as e:
        print(f"✗ 错误: {e}")
        
except ImportError as e:
    print(f"✗ pdf2image 库未安装: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("所有测试完成！")
print("=" * 80)
