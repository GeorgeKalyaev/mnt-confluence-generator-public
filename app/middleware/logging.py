"""Middleware для логирования HTTP запросов"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import time
from app.utils import log_request, log_error, logger, generate_request_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех HTTP запросов"""
    async def dispatch(self, request: StarletteRequest, call_next):
        # Пропускаем статические файлы
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Генерируем request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Получаем IP пользователя
        user_ip = request.client.host if request.client else "unknown"
        request.state.user_ip = user_ip
        
        # Начало запроса
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        logger.debug(
            f"ВХОДЯЩИЙ ЗАПРОС | {method} {path}",
            extra={
                'request_id': request_id,
                'user_ip': user_ip,
                'user_name': '-'
            }
        )
        if query_params:
            logger.debug(
                f"Query params: {query_params}",
                extra={
                    'request_id': request_id,
                    'user_ip': user_ip,
                    'user_name': '-'
                }
            )
        
        # Пытаемся получить размер запроса из заголовков
        request_size_bytes = None
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                request_size_bytes = int(content_length)
            except (ValueError, TypeError):
                pass
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Пытаемся определить размер ответа из заголовков
            response_size_bytes = None
            content_length = response.headers.get('content-length')
            if content_length:
                try:
                    response_size_bytes = int(content_length)
                except (ValueError, TypeError):
                    pass
            
            # Логируем ответ с метриками
            log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                request_id=request_id,
                user_ip=user_ip,
                duration_ms=duration_ms,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes
            )
            
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error(
                error=e,
                context=f"Обработка запроса {method} {path}",
                request_id=request_id,
                user_ip=user_ip
            )
            raise
