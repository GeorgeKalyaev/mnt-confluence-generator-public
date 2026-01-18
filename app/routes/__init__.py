"""Роуты FastAPI приложения"""
# Не импортируем app здесь, чтобы избежать circular imports
# app и templates импортируются напрямую из app.routes.main или через app.__init__.py
# Роутеры импортируются напрямую в функции register_routers() в app.routes.main

__all__ = []
