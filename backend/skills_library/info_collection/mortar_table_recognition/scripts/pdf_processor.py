"""
PDF Processor for Converting PDF to Images
PDF转图片处理器
"""

import logging
from pathlib import Path
from typing import List, Optional

try:
    from pdf2image import convert_from_path
except ImportError:
    raise ImportError("pdf2image is required. Install with: pip install pdf2image")


logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processor for converting PDF files to images."""
    
    def __init__(
        self,
        poppler_path: Optional[str] = None,
        dpi: int = 300,
        output_format: str = 'png'
    ):
        """
        Initialize PDF processor.
        
        Args:
            poppler_path: Path to poppler binaries (Windows only)
            dpi: DPI for image conversion
            output_format: Output image format (png, jpg, etc.)
        """
        self.poppler_path = poppler_path
        self.dpi = dpi
        self.output_format = output_format
    
    def pdf_to_images(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        page_range: Optional[tuple] = None
    ) -> List[str]:
        """
        Convert PDF to images.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save images (defaults to temp dir)
            page_range: Tuple of (first_page, last_page) to convert, 1-indexed
            
        Returns:
            List of paths to generated image files
            
        Raises:
            FileNotFoundError: If PDF file not found
            Exception: If conversion fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Set output directory
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = Path(__file__).parent.parent / 'data' / 'temp'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            
            # Convert PDF to images
            kwargs = {
                'dpi': self.dpi,
                'fmt': self.output_format,
            }
            
            if self.poppler_path:
                kwargs['poppler_path'] = self.poppler_path
            
            if page_range:
                kwargs['first_page'] = page_range[0]
                kwargs['last_page'] = page_range[1]
            
            images = convert_from_path(str(pdf_path), **kwargs)
            
            # Save images and collect paths
            image_paths = []
            base_name = pdf_path.stem
            
            for i, image in enumerate(images, start=1):
                image_path = output_dir / f"{base_name}_page_{i}.{self.output_format}"
                image.save(image_path, self.output_format.upper())
                image_paths.append(str(image_path))
                logger.info(f"Saved page {i} to {image_path}")
            
            logger.info(f"Converted {len(images)} pages from PDF")
            return image_paths
            
        except Exception as e:
            logger.error(f"Failed to convert PDF: {e}")
            raise
    
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
