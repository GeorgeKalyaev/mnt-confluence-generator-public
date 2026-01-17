"""Модуль для логирования операций"""
import logging
import os
import uuid
import json
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

from app.config import settings

# Добавляем уровень TRACE (ниже DEBUG)
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

def trace(self, message, *args, **kws):
    """Метод для логирования на уровне TRACE"""
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)

logging.Logger.trace = trace

# Создаем директорию для логов, если её нет
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Получаем hostname
try:
    hostname = socket.gethostname()
except Exception:
    hostname = "unknown"

# Настройка логирования с расширенным форматом
class ContextFilter(logging.Filter):
    """Фильтр для добавления контекста в логи"""
    def filter(self, record):
        # Добавляем контекстные поля, если их нет
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(record, 'request_id', '-')
        if not hasattr(record, 'user_ip'):
            record.user_ip = getattr(record, 'user_ip', '-')
        if not hasattr(record, 'user_name'):
            record.user_name = getattr(record, 'user_name', '-')
        
        # Добавляем дополнительные поля
        if not hasattr(record, 'hostname'):
            record.hostname = hostname
        if not hasattr(record, 'service_name'):
            record.service_name = settings.log_service_name
        if not hasattr(record, 'environment'):
            record.environment = settings.log_environment
        
        # Метрики (если есть)
        if not hasattr(record, 'duration_ms'):
            record.duration_ms = getattr(record, 'duration_ms', None)
        if not hasattr(record, 'request_size_bytes'):
            record.request_size_bytes = getattr(record, 'request_size_bytes', None)
        if not hasattr(record, 'response_size_bytes'):
            record.response_size_bytes = getattr(record, 'response_size_bytes', None)
        
        return True


class TextFormatter(logging.Formatter):
    """Текстовый форматтер с поддержкой контекста"""
    def format(self, record):
        # Добавляем контекстные поля
        context_parts = []
        if hasattr(record, 'request_id') and record.request_id != '-':
            context_parts.append(f"RequestID={record.request_id}")
        if hasattr(record, 'user_ip') and record.user_ip != '-':
            context_parts.append(f"IP={record.user_ip}")
        if hasattr(record, 'user_name') and record.user_name != '-':
            context_parts.append(f"User={record.user_name}")
        if hasattr(record, 'hostname') and record.hostname != 'unknown':
            context_parts.append(f"Host={record.hostname}")
        if hasattr(record, 'service_name'):
            context_parts.append(f"Service={record.service_name}")
        if hasattr(record, 'environment'):
            context_parts.append(f"Env={record.environment}")
        
        context_str = " | ".join(context_parts) if context_parts else ""
        if context_str:
            record.msg = f"[{context_str}] {record.msg}"
        
        # Добавляем метрики в сообщение
        metrics = []
        if hasattr(record, 'duration_ms') and record.duration_ms is not None:
            metrics.append(f"Duration: {record.duration_ms:.2f}ms")
        if hasattr(record, 'request_size_bytes') and record.request_size_bytes is not None:
            metrics.append(f"RequestSize: {record.request_size_bytes} bytes")
        if hasattr(record, 'response_size_bytes') and record.response_size_bytes is not None:
            metrics.append(f"ResponseSize: {record.response_size_bytes} bytes")
        
        if metrics:
            record.msg += f" | {' | '.join(metrics)}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON форматтер для интеграции с ELK"""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "hostname": getattr(record, 'hostname', hostname),
            "service_name": getattr(record, 'service_name', settings.log_service_name),
            "environment": getattr(record, 'environment', settings.log_environment),
        }
        
        # Добавляем контекст
        if hasattr(record, 'request_id') and record.request_id != '-':
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'user_ip') and record.user_ip != '-':
            log_entry["user_ip"] = record.user_ip
        if hasattr(record, 'user_name') and record.user_name != '-':
            log_entry["user_name"] = record.user_name
        
        # Добавляем метрики
        if hasattr(record, 'duration_ms') and record.duration_ms is not None:
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, 'request_size_bytes') and record.request_size_bytes is not None:
            log_entry["request_size_bytes"] = record.request_size_bytes
        if hasattr(record, 'response_size_bytes') and record.response_size_bytes is not None:
            log_entry["response_size_bytes"] = record.response_size_bytes
        
        # Добавляем дополнительные поля из extra
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName', 'relativeCreated',
                'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                'request_id', 'user_ip', 'user_name', 'hostname', 'service_name',
                'environment', 'duration_ms', 'request_size_bytes', 'response_size_bytes'
            ]:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


# Выбираем форматтер на основе настроек
if settings.log_format.lower() == "json":
    formatter = JSONFormatter()
else:
    formatter = TextFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# Преобразуем строковый уровень в числовой
LOG_LEVELS = {
    "TRACE": TRACE_LEVEL,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level = LOG_LEVELS.get(settings.log_level.upper(), logging.INFO)

# Настройка handlers
handlers = []

# File handler с ротацией
if settings.log_enable_file:
    max_bytes = settings.log_file_max_size_mb * 1024 * 1024  # Конвертируем МБ в байты
    file_handler = RotatingFileHandler(
        log_dir / f"app_{datetime.now().strftime('%Y-%m')}.log",
        maxBytes=max_bytes,
        backupCount=settings.log_file_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    file_handler.addFilter(ContextFilter())
    handlers.append(file_handler)

# Console handler
if settings.log_enable_console:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    console_handler.addFilter(ContextFilter())
    handlers.append(console_handler)

# Настройка логирования
logging.basicConfig(
    level=log_level,
    handlers=handlers,
    force=True  # Переопределяем существующие настройки
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
    user_ip: Optional[str] = None,
    duration_ms: Optional[float] = None
):
    """Логирование операций с МНТ с контекстом"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user,
        'duration_ms': duration_ms
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
    user_name: Optional[str] = None,
    duration_ms: Optional[float] = None
):
    """Логирование операций с Confluence с контекстом"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user_name or '-',
        'duration_ms': duration_ms
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
    url: Optional[str] = None,
    duration_ms: Optional[float] = None
):
    """Логирование действий пользователя"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user,
        'duration_ms': duration_ms
    }
    log_msg = f"ДЕЙСТВИЕ | {action}"
    if url:
        log_msg += f" | URL: {url}"
        extra['url'] = url
    if details:
        log_msg += f" | Детали: {details}"
        extra['details'] = details
    logger.info(log_msg, extra=extra)


def log_request(
    method: str,
    path: str,
    status_code: int,
    request_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_name: Optional[str] = None,
    duration_ms: Optional[float] = None,
    request_size_bytes: Optional[int] = None,
    response_size_bytes: Optional[int] = None
):
    """Логирование HTTP запросов с метриками"""
    extra = {
        'request_id': request_id or '-',
        'user_ip': user_ip or '-',
        'user_name': user_name or '-',
        'duration_ms': duration_ms,
        'request_size_bytes': request_size_bytes,
        'response_size_bytes': response_size_bytes,
        'status_code': status_code,
        'method': method,
        'path': path
    }
    
    # Определяем уровень логирования на основе статуса
    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.DEBUG
    
    log_msg = f"HTTP | {method} {path} | Status: {status_code}"
    logger.log(level, log_msg, extra=extra)
