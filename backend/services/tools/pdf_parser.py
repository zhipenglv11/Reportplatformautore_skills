from __future__ import annotations

from pathlib import Path
from typing import List

from pdf2image import convert_from_path


def pdf_to_images(pdf_path: str | Path) -> List:
    """Convert a PDF file into PIL images."""
    return convert_from_path(str(pdf_path))
