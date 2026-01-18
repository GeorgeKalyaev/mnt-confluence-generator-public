"""Валидация и санитизация входных данных"""
import re
import html
from typing import Any, Dict, List, Optional
from markupsafe import Markup, escape
from app.logger import log_security_event


def sanitize_string(value: Any, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """Санитизация строки от потенциально опасного контента"""
    if value is None:
        return ""
    
    if not isinstance(value, str):
        value = str(value)
    
    # Удаляем управляющие символы (кроме переносов строк и табуляции)
    value = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', value)
    
    # Если HTML не разрешен, экранируем HTML теги
    if not allow_html:
        value = html.escape(value)
    else:
        # Разрешаем только безопасные HTML теги
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li']
        # Базовая проверка на наличие опасных тегов (script, iframe, etc.)
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'on\w+\s*=',  # JavaScript event handlers
            r'javascript:',
            r'data:text/html',
        ]
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
    
    # Обрезка длины
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


def sanitize_dict(data: Dict[str, Any], allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """Санитизация словаря с данными формы"""
    sanitized = {}
    
    for key, value in data.items():
        # Проверка на разрешенные ключи
        if allowed_keys and key not in allowed_keys:
            continue
        
        # Санитизация ключа
        safe_key = sanitize_string(key, max_length=200)
        
        if isinstance(value, str):
            # Для строк определяем, разрешен ли HTML (например, для полей с rich text)
            allow_html = key in ['description', 'introduction_text', 'content'] if 'content' in key.lower() else False
            sanitized[safe_key] = sanitize_string(value, allow_html=allow_html)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_dict(value, allowed_keys=None)
        elif isinstance(value, list):
            sanitized[safe_key] = [sanitize_string(item, allow_html=False) if isinstance(item, str) else item 
                                   for item in value]
        else:
            sanitized[safe_key] = value
    
    return sanitized


def validate_mnt_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Валидация данных МНТ на основе бизнес-правил"""
    
    # Проверка обязательных полей
    required_fields = ['title', 'project', 'author']
    for field in required_fields:
        if not data.get(field) or not isinstance(data.get(field), str) or len(data.get(field).strip()) == 0:
            return False, f"Поле '{field}' обязательно для заполнения"
    
    # Проверка длины полей
    length_limits = {
        'title': 500,
        'project': 200,
        'author': 200,
    }
    
    for field, max_length in length_limits.items():
        value = data.get(field, '')
        if isinstance(value, str) and len(value) > max_length:
            return False, f"Поле '{field}' не должно превышать {max_length} символов"
    
    # Проверка на SQL инъекции в текстовых полях (базовая защита)
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b|\bAND\b)\s*['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
    ]
    
    for key, value in data.items():
        if isinstance(value, str):
            for pattern in sql_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    # Логируем попытку SQL инъекции
                    log_security_event(
                        event_type="sql_injection_attempt",
                        description=f"Обнаружена попытка SQL инъекции в поле '{key}'",
                        severity="high",
                        details={"field": key, "pattern": pattern, "value_sample": value[:100]},
                        user_ip=None,  # Будет передано из вызывающего кода
                        url=None
                    )
                    return False, f"Поле '{key}' содержит потенциально опасный код"
    
    # Проверка на XSS (дополнительная защита)
    xss_patterns = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]
    
    for key, value in data.items():
        if isinstance(value, str):
            for pattern in xss_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    # Логируем попытку XSS
                    log_security_event(
                        event_type="xss_attempt",
                        description=f"Обнаружена попытка XSS атаки в поле '{key}'",
                        severity="high",
                        details={"field": key, "pattern": pattern, "value_sample": value[:100]},
                        user_ip=None,
                        url=None
                    )
                    return False, f"Поле '{key}' содержит потенциально опасный код"
    
    return True, None


def sanitize_search_query(query: str) -> str:
    """Санитизация поискового запроса"""
    if not query:
        return ""
    
    # Удаляем специальные SQL символы
    query = re.sub(r"[%_']", '', query)
    
    # Ограничиваем длину
    query = query[:100]
    
    # Экранируем HTML
    query = html.escape(query)
    
    return query.strip()


def sanitize_file_name(file_name: str) -> str:
    """Санитизация имени файла"""
    if not file_name:
        return "file"
    
    # Удаляем опасные символы
    file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)
    
    # Ограничиваем длину
    file_name = file_name[:255]
    
    return file_name.strip()
