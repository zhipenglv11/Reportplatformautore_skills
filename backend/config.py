# backend/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    db_url: str
    storage_base_path: str = str(PROJECT_ROOT / "data")  # 本地存储根目录（storage_backend=local 时生效）
    llm_provider: str = "qwen"  # openai, siliconflow, qwen, moonshot
    llm_model: str = "qwen3-omni-flash-2025-12-01"
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    openai_api_key: str = ""
    siliconflow_api_key: str = ""
    moonshot_api_key: str = ""
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 已弃用：PDF 转图片已改用 PyMuPDF，无需 Poppler。保留仅为兼容旧环境变量。
    poppler_bin_path: str = ""
    env: str = "development"
    debug: bool = True
    report_demo_mode: bool = False
    report_demo_profile: str = "weifang_v1"

    # CORS：逗号分隔的允许源列表，生产环境设为 Vercel 域名
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # 文件存储后端：local（本地磁盘）或 supabase（Supabase Storage）
    storage_backend: str = "local"
    supabase_url: str = ""              # 例如 https://xxxx.supabase.co
    supabase_service_role_key: str = "" # Supabase service_role 密钥
    supabase_storage_bucket: str = "uploads"  # Supabase Storage bucket 名称

    # 声明式 Skills 配置（相对 config 所在目录，Railway 以 backend 为根时仍能正确找到 skills_library）
    declarative_skills_path: str = str(Path(__file__).resolve().parent / "skills_library")
    enable_declarative_skills: bool = True
  
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

