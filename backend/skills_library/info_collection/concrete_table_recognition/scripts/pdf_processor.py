"""
PDF处理模块（PyMuPDF，无需 Poppler）
将PDF文件转换为图片
"""

import sys
from pathlib import Path
from typing import List, Optional

from scripts.config import TEMP_DIR, SUPPORTED_PDF_FORMATS

# 确保从 backend 根目录或脚本目录运行时能导入 services
_backend = Path(__file__).resolve().parents[4]
if _backend not in sys.path:
    sys.path.insert(0, str(_backend))

from services.tools.pdf_to_image import pdf_to_images as pdf_to_pil_images


def pdf_to_images(
    pdf_path: Path, output_dir: Optional[Path] = None, dpi: int = 150
) -> List[Path]:
    """
    将PDF文件转换为图片（PyMuPDF，无需系统 Poppler）。
    """
    if output_dir is None:
        output_dir = TEMP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    images = pdf_to_pil_images(str(pdf_path), dpi=dpi)
    image_paths = []
    pdf_name = pdf_path.stem
    for i, image in enumerate(images):
        image_path = output_dir / f"{pdf_name}_page_{i + 1}.png"
        image.thumbnail((2000, 2000))
        image.save(image_path, "PNG", optimize=True, compress_level=9)
        image_paths.append(image_path)
    return image_paths


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
