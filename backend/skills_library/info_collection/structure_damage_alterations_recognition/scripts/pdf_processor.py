"""
PDF Processor
PDF处理模块
"""

import os
from pathlib import Path
from typing import List, Optional
from pdf2image import convert_from_path
from PIL import Image


class PDFProcessor:
    """PDF处理器"""

    def __init__(self, poppler_path: Optional[str] = None,
                 temp_dir: Optional[str] = None):
        """
        初始化处理器
        
        Args:
            poppler_path: Poppler二进制文件路径
            temp_dir: 临时文件目录
        """
        self.poppler_path = poppler_path
        self.temp_dir = Path(temp_dir) if temp_dir else Path('data/temp')
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def convert_pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[str]:
        """
        将PDF转换为图片
        
        Args:
            pdf_path: PDF文件路径
            dpi: 图片分辨率
            
        Returns:
            图片路径列表
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 转换PDF为图片
        images = convert_from_path(
            str(pdf_path),
            dpi=dpi,
            poppler_path=self.poppler_path
        )

        # 保存图片
        image_paths = []
        base_name = pdf_path.stem

        for i, image in enumerate(images):
            image_path = self.temp_dir / f"{base_name}_page_{i+1}.png"
            image.save(image_path, 'PNG')
            image_paths.append(str(image_path))

        return image_paths

    def is_pdf(self, file_path: str) -> bool:
        """
        判断是否为PDF文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为PDF
        """
        return Path(file_path).suffix.lower() == '.pdf'

    def is_image(self, file_path: str) -> bool:
        """
        判断是否为图片文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为图片
        """
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
        return Path(file_path).suffix.lower() in image_extensions

    def validate_image(self, image_path: str) -> tuple[bool, Optional[str]]:
        """
        验证图片文件
        
        Args:
            image_path: 图片路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                return False, "文件不存在"
            
            # 尝试打开图片
            with Image.open(image_path) as img:
                # 检查图片格式
                if img.format not in ['PNG', 'JPEG', 'BMP', 'GIF', 'TIFF']:
                    return False, f"不支持的图片格式: {img.format}"
                
                # 检查图片尺寸
                width, height = img.size
                if width < 100 or height < 100:
                    return False, f"图片尺寸过小: {width}x{height}"
            
            return True, None

        except Exception as e:
            return False, f"图片验证失败: {str(e)}"

    def cleanup_temp_files(self, keep_recent: int = 0) -> int:
        """
        清理临时文件
        
        Args:
            keep_recent: 保留最近N个文件
            
        Returns:
            删除的文件数量
        """
        if not self.temp_dir.exists():
            return 0

        # 获取所有临时文件
        temp_files = sorted(
            self.temp_dir.glob('*'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # 删除旧文件
        deleted_count = 0
        for file_path in temp_files[keep_recent:]:
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception:
                pass

        return deleted_count
