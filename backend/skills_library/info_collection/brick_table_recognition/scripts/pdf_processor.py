"""
PDF processing utilities (PyMuPDF, no Poppler).
Convert PDF pages to images.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

from scripts.config import TEMP_DIR, SUPPORTED_PDF_FORMATS

# 确保从 backend 根目录运行时能导入 services
_backend = Path(__file__).resolve().parents[4]
if _backend not in sys.path:
    sys.path.insert(0, str(_backend))

from services.tools.pdf_to_image import pdf_to_images as pdf_to_pil_images


def pdf_to_images(
    pdf_path: Path, output_dir: Optional[Path] = None, dpi: int = 150
) -> List[Path]:
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
    return file_path.suffix.lower() in SUPPORTED_PDF_FORMATS


def process_file(file_path: Path) -> List[Path]:
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if is_pdf_file(file_path):
        return pdf_to_images(file_path)

    return [file_path]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <pdf_file>")
        sys.exit(1)

    pdf_file = Path(sys.argv[1])
    images = pdf_to_images(pdf_file)
    print(f"Converted {len(images)} page(s)")
    for img in images:
        print(f"   {img}")
