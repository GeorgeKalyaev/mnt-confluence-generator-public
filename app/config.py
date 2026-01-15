"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # Database
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "mnt_db"
    database_user: str = "postgres"
    database_password: str = "postgres"
    
    # Confluence
    confluence_url: str = "https://your-confluence.atlassian.net"
    confluence_email: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
