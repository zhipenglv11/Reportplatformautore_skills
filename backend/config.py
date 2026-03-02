# backend/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    db_url: str
    storage_base_path: str = str(PROJECT_ROOT / "data")  # 本地存储根目录
    llm_provider: str = "qwen"  # openai, siliconflow, qwen, moonshot
    llm_model: str = "qwen3-omni-flash-2025-12-01"  # qwen3-omni-flash-2025-12-01, qwen3-omni-flash-2025-12-01, qwen3-omni-flash-2025-12-01
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    openai_api_key: str = ""
    siliconflow_api_key: str = ""  # 硅基流动API Key（可选）
    moonshot_api_key: str = ""  # Moonshot API Key（可选）
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    qwen_api_key: str = ""  # DashScope API Key（可选）
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 已弃用：PDF 转图片已改用 PyMuPDF，无需 Poppler。保留仅为兼容旧环境变量。
    poppler_bin_path: str = ""
    env: str = "development"
    debug: bool = True
    
    # 声明式 Skills 配置
    declarative_skills_path: str = str(PROJECT_ROOT / "backend" / "skills_library")  # 声明式 Skills 基础目录
    enable_declarative_skills: bool = True  # 是否启用声明式 Skills
  
    class Config:
        env_file = ".env"
  
    @property
    def uploads_path(self) -> Path:
        """上传文件存储路径"""
        return Path(self.storage_base_path) / "uploads"
  
    @property
    def parsed_path(self) -> Path:
        """解析结果存储路径"""
        return Path(self.storage_base_path) / "parsed"

settings = Settings()

