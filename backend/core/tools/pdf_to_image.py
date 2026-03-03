# -*- coding: utf-8 -*-
"""
PDF 转图片：使用 PyMuPDF（纯 Python 依赖，无需系统 Poppler）。
适用于 Vercel/Railway 等无系统级依赖的部署环境。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore


def pdf_to_images(
    pdf_path: Union[str, Path],
    dpi: int = 200,
    first_page: Optional[int] = None,
    last_page: Optional[int] = None,
) -> List[Image.Image]:
    """
    将 PDF 转为 PIL Image 列表。不依赖 Poppler，仅需 pip install pymupdf。

    Args:
        pdf_path: PDF 文件路径
        dpi: 输出分辨率，默认 200
        first_page: 起始页（1-based），None 表示从第 1 页
        last_page: 结束页（1-based），None 表示到最后一页

    Returns:
        PIL.Image 列表，每页一张图

    Raises:
        RuntimeError: 未安装 pymupdf
        FileNotFoundError: PDF 不存在
    """
    if fitz is None:
        raise RuntimeError(
            "PDF 转图片需要安装 PyMuPDF，请执行: pip install pymupdf"
        )
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    try:
        start = (first_page - 1) if first_page is not None else 0
        end = last_page if last_page is not None else len(doc)
        start = max(0, start)
        end = min(end, len(doc))
        images: List[Image.Image] = []
        for i in range(start, end):
            page = doc[i]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )
            images.append(img)
        return images
    finally:
        doc.close()
