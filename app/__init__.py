"""МНТ Confluence Generator - веб-приложение для создания и публикации документов МНТ"""

# Для обратной совместимости экспортируем основные модули
from app.core import settings, get_db, check_connection
from app.routes.main import app as fastapi_app

# Экспортируем app для обратной совместимости
app = fastapi_app

__version__ = "1.0.0"
__all__ = ['app', 'fastapi_app', 'settings', 'get_db', 'check_connection']
