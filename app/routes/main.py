"""Главный файл приложения FastAPI - создание app и базовые роуты"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import os

# Core
from app.core import check_connection

# Utils
from app.utils import (
    AppException, NotFoundError, AppValidationError, DatabaseError, ConfluenceError, SecurityError,
    app_exception_handler, validation_exception_handler, database_exception_handler, general_exception_handler,
    logger
)

# Services
from app.services import start_scheduler_async

# Middleware
from app.middleware import LoggingMiddleware

# Создание FastAPI приложения
app = FastAPI(title="МНТ Confluence Generator", version="1.0.0")

# Подключение обработчиков исключений
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Подключение шаблонов (для использования в других роутерах)
templates = Jinja2Templates(directory="app/templates")

__all__ = ['app', 'templates']

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем middleware
app.add_middleware(LoggingMiddleware)


@app.on_event("startup")
async def startup_event():
    """Проверка подключения к БД при старте и запуск планировщика"""
    if not check_connection():
        logger.warning("Database connection failed!")
    
    # Запускаем планировщик автоматических бэкапов
    await start_scheduler_async()


@app.get("/favicon.ico")
async def favicon():
    """Обработчик для favicon.ico - возвращает SVG favicon"""
    favicon_path = os.path.join("app", "static", "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница - редирект на список"""
    return RedirectResponse(url="/mnt/list")


# Импортируем и регистрируем роутеры из других модулей
# Это делается в конце файла, чтобы избежать circular imports
def register_routers():
    """Регистрация всех роутеров приложения"""
    from app.routes.mnt import router as mnt_router
    from app.routes.api import router as api_router
    from app.routes.admin import router as admin_router, api_admin_router
    
    # Регистрируем роутеры
    app.include_router(mnt_router)
    app.include_router(api_router)
    app.include_router(admin_router)
    # Регистрируем API роуты для админ функций (теги)
    app.include_router(api_admin_router)


# Регистрируем роутеры
register_routers()
