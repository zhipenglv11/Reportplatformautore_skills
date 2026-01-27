"""
Configuration Management
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """配置管理器"""

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            env_file: .env文件路径(默认为项目根目录下的.env)
        """
        # 加载环境变量
        if env_file:
            load_dotenv(env_file)
        else:
            # 尝试在项目根目录查找.env
            project_root = Path(__file__).parent.parent
            env_path = project_root / '.env'
            if env_path.exists():
                load_dotenv(env_path)

        # API Keys
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        # Keep compatibility with brick .env which uses QWEN_API_KEY
        self.dashscope_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('QWEN_API_KEY')

        # 模型配置
        self.default_model = os.getenv('DEFAULT_MODEL', 'qwen')
        self.qwen_model = os.getenv('QWEN_MODEL', 'qwen-vl-max-latest')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')

        # 处理配置
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('TIMEOUT', '60'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '10'))

        # Poppler路径(用于PDF转换)
        self.poppler_path = os.getenv('POPPLER_PATH', './poppler-24.08.0/Library/bin')

        # 输出配置
        self.default_output_dir = os.getenv('DEFAULT_OUTPUT_DIR', 'data/output')
        self.default_output_format = os.getenv('DEFAULT_OUTPUT_FORMAT', 'json')

        # 路径
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / 'data'
        self.output_dir = self.project_root / self.default_output_dir
        self.temp_dir = self.data_dir / 'temp'

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证配置
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 检查API Keys
        if not self.dashscope_api_key and not self.anthropic_api_key:
            errors.append("未配置API Key: 请设置 DASHSCOPE_API_KEY 或 ANTHROPIC_API_KEY")

        # 检查默认模型
        if self.default_model not in ['qwen', 'claude']:
            errors.append(f"无效的默认模型: {self.default_model} (应为 'qwen' 或 'claude')")

        # 检查Qwen API Key
        if self.default_model == 'qwen' and not self.dashscope_api_key:
            errors.append("使用Qwen模型需要配置 DASHSCOPE_API_KEY")

        # 检查Claude API Key
        if self.default_model == 'claude' and not self.anthropic_api_key:
            errors.append("使用Claude模型需要配置 ANTHROPIC_API_KEY")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_model_config(self, model: Optional[str] = None) -> dict:
        """
        获取模型配置
        
        Args:
            model: 模型名称(None则使用默认)
            
        Returns:
            模型配置字典
        """
        model = model or self.default_model

        if model == 'qwen':
            return {
                'model': model,
                'model_name': self.qwen_model,
                'api_key': self.dashscope_api_key,
                'max_retries': self.max_retries,
                'timeout': self.timeout
            }
        elif model == 'claude':
            return {
                'model': model,
                'model_name': self.claude_model,
                'api_key': self.anthropic_api_key,
                'max_retries': self.max_retries,
                'timeout': self.timeout
            }
        else:
            raise ValueError(f"不支持的模型: {model}")

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"Config(\n"
            f"  default_model={self.default_model},\n"
            f"  qwen_model={self.qwen_model},\n"
            f"  claude_model={self.claude_model},\n"
            f"  output_dir={self.output_dir},\n"
            f"  has_dashscope_key={bool(self.dashscope_api_key)},\n"
            f"  has_anthropic_key={bool(self.anthropic_api_key)}\n"
            f")"
        )
