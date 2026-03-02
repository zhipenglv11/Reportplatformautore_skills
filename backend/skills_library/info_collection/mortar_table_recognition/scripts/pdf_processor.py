"""
PDF Processor for Converting PDF to Images (uses PyMuPDF, no Poppler).
PDF转图片处理器
"""

import logging
from pathlib import Path
from typing import List, Optional

from services.tools.pdf_to_image import pdf_to_images as pdf_to_pil_images

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processor for converting PDF files to images (PyMuPDF-based)."""

    def __init__(
        self,
        poppler_path: Optional[str] = None,
        dpi: int = 300,
        output_format: str = 'png'
    ):
        """
        Initialize PDF processor.
        poppler_path 已弃用，保留参数仅为兼容调用方。
        """
        self.dpi = dpi
        self.output_format = output_format

    def pdf_to_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        page_range: Optional[tuple] = None
    ) -> List[str]:
        """
        Convert PDF to images (PyMuPDF, no system Poppler required).
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = Path(__file__).parent.parent / 'data' / 'temp'
        output_dir.mkdir(parents=True, exist_ok=True)

        first_page, last_page = (page_range[0], page_range[1]) if page_range else (None, None)
        images = pdf_to_pil_images(
            str(pdf_path),
            dpi=self.dpi,
            first_page=first_page,
            last_page=last_page,
        )

        image_paths = []
        base_name = pdf_path.stem
        for i, image in enumerate(images, start=1):
            image_path = output_dir / f"{base_name}_page_{i}.{self.output_format}"
            image.save(image_path, self.output_format.upper())
            image_paths.append(str(image_path))
            logger.info(f"Saved page {i} to {image_path}")
        logger.info(f"Converted {len(images)} pages from PDF")
        return image_paths
    
    def is_pdf(self, file_path: str) -> bool:
        """
        Check if file is a PDF.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is PDF
        """
        return Path(file_path).suffix.lower() == '.pdf'
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get number of pages in PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except ImportError:
            # Fallback: convert and count
            images = self.pdf_to_images(pdf_path)
            return len(images)
