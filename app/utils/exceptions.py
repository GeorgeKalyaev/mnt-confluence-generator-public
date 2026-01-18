"""Централизованная обработка исключений и ошибок"""
from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback
from typing import Optional

from app.utils.logger import log_error, logger, generate_request_id


class AppException(Exception):
    """Базовое исключение приложения"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Ресурс не найден"""
    def __init__(self, message: str = "Ресурс не найден", details: Optional[dict] = None):
        super().__init__(message, status_code=404, details=details)


class AppValidationError(AppException):
    """Ошибка валидации данных"""
    def __init__(self, message: str = "Ошибка валидации данных", details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)


class DatabaseError(AppException):
    """Ошибка базы данных"""
    def __init__(self, message: str = "Ошибка базы данных", details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class ConfluenceError(AppException):
    """Ошибка при работе с Confluence"""
    def __init__(self, message: str = "Ошибка при работе с Confluence", details: Optional[dict] = None):
        super().__init__(message, status_code=502, details=details)


class SecurityError(AppException):
    """Ошибка безопасности"""
    def __init__(self, message: str = "Ошибка безопасности", details: Optional[dict] = None):
        super().__init__(message, status_code=403, details=details)


async def app_exception_handler(request: Request, exc: AppException):
    """Обработчик пользовательских исключений приложения"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    # Логируем ошибку
    log_error(
        error=exc,
        context=f"{request.method} {request.url.path}",
        details={
            **exc.details,
            "status_code": exc.status_code
        },
        request_id=request_id,
        user_ip=user_ip
    )
    
    # Если это HTML запрос, возвращаем HTML ответ
    if "text/html" in request.headers.get("accept", ""):
        from app.routes.main import templates
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": exc.message,
            "error_code": exc.status_code,
            "request_id": request_id
        }, status_code=exc.status_code)
    
    # Для API запросов возвращаем JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
            "path": str(request.url.path)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
    
    user_message = "Ошибка валидации данных. Проверьте правильность заполнения полей."
    if len(error_messages) == 1:
        user_message = error_messages[0]
    
    log_error(
        error=exc,
        context=f"{request.method} {request.url.path}",
        details={
            "validation_errors": errors,
            "error_messages": error_messages
        },
        request_id=request_id,
        user_ip=user_ip
    )
    
    if "text/html" in request.headers.get("accept", ""):
        from app.routes.main import templates
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": user_message,
            "error_code": 400,
            "request_id": request_id
        }, status_code=400)
    
    return JSONResponse(
        status_code=400,
        content={
            "error": True,
            "message": user_message,
            "validation_errors": errors,
            "request_id": request_id
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Обработчик ошибок базы данных"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    # Детальная информация для логирования
    error_details = {
        "error_type": type(exc).__name__,
        "error_message": str(exc)
    }
    
    # Если это ошибка целостности (например, нарушение уникальности)
    if isinstance(exc, IntegrityError):
        error_details["integrity_error"] = True
        user_message = "Ошибка базы данных: нарушение целостности данных"
    else:
        user_message = "Произошла ошибка при работе с базой данных"
    
    log_error(
        error=exc,
        context=f"{request.method} {request.url.path}",
        details=error_details,
        request_id=request_id,
        user_ip=user_ip
    )
    
    if "text/html" in request.headers.get("accept", ""):
        from app.routes.main import templates
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": user_message,
            "error_code": 500,
            "request_id": request_id
        }, status_code=500)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": user_message,
            "request_id": request_id
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик всех остальных исключений"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    # Получаем полный traceback
    tb_str = "".join(traceback.format_tb(exc.__traceback__))
    
    log_error(
        error=exc,
        context=f"{request.method} {request.url.path}",
        details={
            "error_type": type(exc).__name__,
            "traceback": tb_str
        },
        request_id=request_id,
        user_ip=user_ip
    )
    
    user_message = "Произошла внутренняя ошибка сервера. Обратитесь к администратору."
    
    if "text/html" in request.headers.get("accept", ""):
        from app.routes.main import templates
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": user_message,
            "error_code": 500,
            "request_id": request_id
        }, status_code=500)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": user_message,
            "request_id": request_id
        }
    )
