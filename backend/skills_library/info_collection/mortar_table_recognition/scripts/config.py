"""
Configuration Management
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the extraction system."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in project root
            project_root = Path(__file__).parent.parent
            env_path = project_root / '.env'
            if env_path.exists():
                load_dotenv(env_path)
        
        # API Keys
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        # Keep compatibility with brick .env which uses QWEN_API_KEY
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')
        
        # Model Configuration
        self.default_model = os.getenv('DEFAULT_MODEL', 'qwen')
        self.qwen_model = os.getenv('QWEN_MODEL', 'qwen-vl-max-latest')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        
        # Processing Configuration
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('TIMEOUT', '60'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))
        # PDF 页面上限，避免整本 PDF 全量 OCR 导致耗时过长
        self.max_pdf_pages = int(os.getenv('MORTAR_MAX_PDF_PAGES', '3'))
        
        # Poppler Path (for PDF conversion)
        # Get backend root directory (up 4 levels from config.py)
        backend_root = Path(__file__).parent.parent.parent.parent.parent
        default_poppler = backend_root / 'poppler-windows' / 'Release-25.12.0-0' / 'poppler-25.12.0' / 'Library' / 'bin'
        self.poppler_path = os.getenv('POPPLER_PATH', str(default_poppler))
        
        # Paths
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.output_dir = self.data_dir / 'output'
        self.temp_dir = self.data_dir / 'temp'
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        if self.default_model == 'claude' and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when using Claude")
        
        if self.default_model == 'qwen' and not self.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required when using Qwen")
        
        return True
    
    def get_model_config(self, model: Optional[str] = None) -> dict:
        """
        Get configuration for specified model.
        
        Args:
            model: Model name ('claude' or 'qwen'), defaults to DEFAULT_MODEL
            
        Returns:
            Model configuration dictionary
        """
        model = model or self.default_model
        
        if model == 'claude':
            return {
                'type': 'claude',
                'model_name': self.claude_model,
                'api_key': self.anthropic_api_key,
                'timeout': self.timeout
            }
        elif model == 'qwen':
            return {
                'type': 'qwen',
                'model_name': self.qwen_model,
                'api_key': self.dashscope_api_key,
                'timeout': self.timeout
            }
        else:
            raise ValueError(f"Unknown model type: {model}")
