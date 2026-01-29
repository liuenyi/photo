from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    应用配置
    """
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./photos.db"
    
    # JWT 配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7天
    
    # CORS 配置
    cors_origins: List[str] = ["*"]
    
    # 文件上传配置
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    upload_dir: str = "uploads"
    
    # 默认密码 - 支持多个密码
    default_password: str = "0525"
    allowed_passwords: List[str] = ["0525", "1234"]  # 支持多个密码，1234用于测试
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建设置实例
settings = Settings() 