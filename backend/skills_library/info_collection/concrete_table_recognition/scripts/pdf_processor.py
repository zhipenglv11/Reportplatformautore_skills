"""
PDF处理模块
将PDF文件转换为图片
"""

import sys
import io
from pathlib import Path
from typing import List, Optional
from pdf2image import convert_from_path
from PIL import Image

from scripts.config import TEMP_DIR, SUPPORTED_PDF_FORMATS

# 本地Poppler路径（Windows）
POPPLER_PATH = Path(__file__).parent.parent / "poppler-24.08.0" / "Library" / "bin"

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def pdf_to_images(
    pdf_path: Path, output_dir: Optional[Path] = None, dpi: int = 150
) -> List[Path]:
    """
    将PDF文件转换为图片

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录，默认为临时目录
        dpi: 图片分辨率，默认150（降低以避免API限制）

    Returns:
        生成的图片文件路径列表
    """
    if output_dir is None:
        output_dir = TEMP_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 转换PDF为图片（使用本地Poppler）
        if POPPLER_PATH.exists():
            images = convert_from_path(
                pdf_path, dpi=dpi, poppler_path=str(POPPLER_PATH)
            )
        else:
            images = convert_from_path(pdf_path, dpi=dpi)

        # 保存图片
        image_paths = []
        pdf_name = pdf_path.stem

        for i, image in enumerate(images):
            image_path = output_dir / f"{pdf_name}_page_{i + 1}.png"
            # 压缩图片，确保不超过5MB（避免API限制）
            image.thumbnail((2000, 2000))  # 限制最大尺寸
            image.save(image_path, "PNG", optimize=True, compress_level=9)
            image_paths.append(image_path)

        return image_paths
    except Exception as e:
        raise Exception(f"PDF转换失败: {str(e)}")


def is_pdf_file(file_path: Path) -> bool:
    """检查文件是否为PDF"""
    return file_path.suffix.lower() in SUPPORTED_PDF_FORMATS


def process_file(file_path: Path) -> List[Path]:
    """
    处理文件（PDF转图片，图片直接返回）

    Args:
        file_path: 文件路径

    Returns:
        图片文件路径列表
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if is_pdf_file(file_path):
        # PDF文件，转换为图片
        return pdf_to_images(file_path)
    else:
        # 图片文件，直接返回
        return [file_path]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pdf_processor.py <pdf_file>")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    images = pdf_to_images(pdf_file)
    print(f"✅ 转换完成，生成 {len(images)} 张图片:")
    for img in images:
        print(f"   {img}")
