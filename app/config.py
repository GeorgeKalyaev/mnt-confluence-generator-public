"""Конфигурация приложения

ВСЕ НАСТРОЙКИ В ОДНОМ МЕСТЕ - config.py

Как это работает:
- Настройки можно изменить прямо в этом файле (значения по умолчанию)
- ИЛИ через переменные окружения системы
- .env файл НЕ используется - всё в одном месте!

Для изменения настроек:
1. Откройте этот файл (app/config.py)
2. Измените нужные значения
3. Перезапустите приложение
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения
    
    Все настройки здесь. Меняйте значения по умолчанию или используйте переменные окружения.
    """
    
    # ============================================
    # Database Configuration (ОБЯЗАТЕЛЬНО)
    # ============================================
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "mnt_db"
    database_user: str = "postgres"
    database_password: str = "postgres"  # ⚠️ ИЗМЕНИТЕ НА СВОЙ ПАРОЛЬ!
    
    # ============================================
    # Confluence Configuration (ОПЦИОНАЛЬНО)
    # ============================================
    # Для Confluence Server/Datacenter (локальный):
    confluence_url: str = "http://localhost:8090"  # URL вашего Confluence Server
    confluence_username: str = "admin"  # Имя пользователя для Server
    confluence_password: str = "admin"  # Пароль для Server
    
    # Для Confluence Cloud (если используете Cloud, заполните эти поля):
    confluence_email: Optional[str] = None  # Email для Cloud
    confluence_api_token: Optional[str] = None  # API Token для Cloud
    
    # ============================================
    # Logging Configuration (Настройки логирования)
    # ============================================
    log_level: str = "INFO"  # Уровень логирования: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"  # Формат логов: "text" (обычный) или "json" (для ELK/Kibana)
    log_service_name: str = "mnt-confluence-generator"  # Название сервиса (для идентификации в логах)
    log_environment: str = "development"  # Окружение: "development", "staging", "production"
    log_file_max_size_mb: int = 100  # Максимальный размер лог-файла в МБ (перед ротацией)
    log_file_backup_count: int = 5  # Количество резервных копий лог-файлов (при ротации)
    log_enable_file: bool = True  # Включить логирование в файл (logs/app_YYYY-MM.log)
    log_enable_console: bool = True  # Включить логирование в консоль
    
    # ============================================
    # Backup Configuration (Автоматические бэкапы)
    # ============================================
    backup_enabled: bool = True  # Включить автоматические бэкапы
    backup_time: str = "02:00"  # Время создания бэкапа (HH:MM)
    backup_retention_days: int = 30  # Хранить бэкапы N дней
    
    class Config:
        # НЕ используем .env файл - все настройки здесь в config.py
        # Можно использовать переменные окружения системы
        case_sensitive = False  # DATABASE_HOST = database_host


settings = Settings()
