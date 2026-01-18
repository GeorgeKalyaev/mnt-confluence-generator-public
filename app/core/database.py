"""Подключение к базе данных"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import psycopg2

# Создание движка SQLAlchemy
DATABASE_URL = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Получение сессии БД (dependency для FastAPI)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection():
    """Проверка подключения к БД"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger("mnt_generator.database")
        logger.error(f"Database connection error: {e}", exc_info=True)
        return False
