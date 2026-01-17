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
    
    # Logging
    log_level: str = "INFO"  # TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"  # "text" или "json" (для ELK)
    log_service_name: str = "mnt-confluence-generator"
    log_environment: str = "development"  # development, staging, production
    log_file_max_size_mb: int = 100  # Максимальный размер лог-файла в МБ
    log_file_backup_count: int = 5  # Количество резервных копий файлов
    log_enable_file: bool = True  # Логирование в файл
    log_enable_console: bool = True  # Логирование в консоль
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
