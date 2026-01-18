"""Pytest конфигурация и фикстуры"""
import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Фикстура для тестового клиента FastAPI"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Фикстура для тестовой сессии БД"""
    # TODO: Настроить тестовую БД при необходимости
    pass
