"""
鉴定内容和方法及原始记录一览表 - 实现模块
"""

from .generate import (
    generate_inspection_content_and_methods,
    generate_inspection_content_and_methods_async
)

__all__ = [
    "generate_inspection_content_and_methods",
    "generate_inspection_content_and_methods_async"
]
