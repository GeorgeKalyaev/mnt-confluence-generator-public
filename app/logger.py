"""Модуль для логирования операций"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Создаем директорию для логов, если её нет
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Настройка логирования с расширенным форматом
class ContextFilter(logging.Filter):
    """Фильтр для добавления контекста в логи"""
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(record, 'request_id', '-')
        if not hasattr(record, 'user_ip'):
            record.user_ip = getattr(record, 'user_ip', '-')
        if not hasattr(record, 'user_name'):
            record.user_name = getattr(record, 'user_name', '-')
        return True

# Создаем кастомный форматтер
class ContextFormatter(logging.Formatter):
    """Форматтер с поддержкой контекста"""
    def format(self, record):
        # Добавляем контекстные поля
        context_parts = []
        if hasattr(record, 'request_id') and record.request_id != '-':
            context_parts.append(f"RequestID={record.request_id}")
        if hasattr(record, 'user_ip') and record.user_ip != '-':
            context_parts.append(f"IP={record.user_ip}")
        if hasattr(record, 'user_name') and record.user_name != '-':
            context_parts.append(f"User={record.user_name}")
        
        context_str = " | ".join(context_parts) if context_parts else ""
        if context_str:
            record.msg = f"[{context_str}] {record.msg}"
        
        return super().format(record)

# Настройка логирования
formatter = ContextFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = logging.FileHandler(
    log_dir / f"app_{datetime.now().strftime('%Y-%m')}.log", 
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.addFilter(ContextFilter())

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.addFilter(ContextFilter())

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger("mnt_generator")

# Генератор request ID
def generate_request_id() -> str:
    """Генерирует уникальный ID для запроса"""
    return str(uuid.uuid4())[:8]

def log_mnt_operation(
    operation: str, 
    mnt_id: int, 
    user: str = "unknown", 
    details: dict = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None
):
    """Логирование операций с МНТ с контекстом"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user
    }
    log_msg = f"МНТ #{mnt_id} | {operation}"
    if details:
        log_msg += f" | Детали: {details}"
    logger.info(log_msg, extra=extra)

def log_error(
    error: Exception, 
    context: str = "", 
    details: dict = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_name: Optional[str] = None
):
    """Логирование ошибок с контекстом"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user_name or '-'
    }
    log_msg = f"ОШИБКА | {context} | {type(error).__name__}: {str(error)}"
    if details:
        log_msg += f" | Детали: {details}"
    logger.error(log_msg, exc_info=True, extra=extra)

def log_confluence_operation(
    operation: str, 
    mnt_id: int, 
    success: bool, 
    details: dict = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_name: Optional[str] = None
):
    """Логирование операций с Confluence с контекстом"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user_name or '-'
    }
    status = "УСПЕХ" if success else "ОШИБКА"
    log_msg = f"Confluence | МНТ #{mnt_id} | {operation} | {status}"
    if details:
        log_msg += f" | Детали: {details}"
    if success:
        logger.info(log_msg, extra=extra)
    else:
        logger.error(log_msg, extra=extra)

def log_user_action(
    action: str,
    user: str = "unknown",
    details: dict = None,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    url: Optional[str] = None
):
    """Логирование действий пользователя"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user
    }
    log_msg = f"ДЕЙСТВИЕ | {action}"
    if url:
        log_msg += f" | URL: {url}"
    if details:
        log_msg += f" | Детали: {details}"
    logger.info(log_msg, extra=extra)

def log_request(
    method: str,
    path: str,
    status_code: int,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_name: Optional[str] = None,
    duration_ms: Optional[float] = None
):
    """Логирование HTTP запросов"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user_name or '-'
    }
    log_msg = f"HTTP | {method} {path} | Status: {status_code}"
    if duration_ms:
        log_msg += f" | Duration: {duration_ms:.2f}ms"
    logger.debug(log_msg, extra=extra)
