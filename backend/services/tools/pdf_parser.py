from __future__ import annotations

from pathlib import Path
from typing import List

from PIL import Image

from services.tools.pdf_to_image import pdf_to_images as _pdf_to_images


def pdf_to_images(pdf_path: str | Path) -> List[Image.Image]:
    """Convert a PDF file into PIL images (uses PyMuPDF, no Poppler required)."""
    return _pdf_to_images(str(pdf_path))
