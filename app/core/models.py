"""Модели данных"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MNTStatus(str, Enum):
    """Статусы МНТ"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ERROR = "error"


class MNTData(BaseModel):
    """Модель данных формы МНТ - новая структура"""
    
    # Заголовок (для шапки документа)
    project_name: str = Field(..., description="Название проекта")
    organization_name: str = Field(..., description="Название компании")
    system_version: str = Field(..., description="Версия системы")
    
    # Раздел 1: История изменений (таблица)
    history_changes_table: Optional[str] = Field(None, description="Таблица истории изменений (Дата|Версия|Описание|Автор)")
    
    # Раздел 2: Лист согласования (таблица)
    approval_list_table: Optional[str] = Field(None, description="Таблица листа согласования (ФИО|Должность|Подпись|Дата)")
    
    # Раздел 3: Сокращения и терминология
    # 3.1 Сокращения (таблица с предзаполненными данными)
    abbreviations_table: Optional[str] = Field(None, description="Таблица сокращений (Наименование сокращения|Описание)")
    
    # 3.2 Терминология (таблица с предзаполненными данными)
    terminology_table: Optional[str] = Field(None, description="Таблица терминологии (Термин|Определение)")
    
    # Раздел 4: Введение
    introduction_text: Optional[str] = Field(None, description="Текст введения")
    
    # Раздел 5: Цели и задачи НТ
    # 5.1 Цели НТ
    goals_business: Optional[str] = Field(None, description="Бизнес-цели (маркированный список)")
    goals_technical: Optional[str] = Field(None, description="Технические цели (маркированный список)")
    
    # 5.2 Задачи НТ
    tasks_nt: Optional[str] = Field(None, description="Задачи НТ (нумерованный список)")
    
    # Раздел 6: Ограничения и риски НТ
    # 6.1 Ограничения НТ
    limitations_list: Optional[str] = Field(None, description="Список ограничений (нумерованный список)")
    
    # 6.2 Риски НТ (таблица)
    risks_table: Optional[str] = Field(None, description="Таблица рисков (Риск|Вероятность возникновения|Влияние)")
    
    # Раздел 7: Объект НТ
    # 7.1 Общие сведения
    object_general: Optional[str] = Field(None, description="Общие сведения об объекте НТ")
    
    # 7.2 Требования к производительности
    performance_requirements: Optional[str] = Field(None, description="Требования к производительности (маркированный список)")
    
    # 7.3 Архитектура системы
    # 7.3.1 Компонентная архитектура
    component_architecture_text: Optional[str] = Field(None, description="Текст компонентной архитектуры (маркированный список)")
    component_architecture_image: Optional[str] = Field(None, description="Имя файла изображения компонентной архитектуры")
    
    # 7.3.2 Информационная архитектура
    information_architecture_image: Optional[str] = Field(None, description="Имя файла изображения информационной архитектуры")
    
    # Раздел 8: Тестовый и промышленный стенды
    # 8.1 Архитектура тестового стенда
    test_stand_architecture_text: Optional[str] = Field(None, description="Текст архитектуры тестового стенда")
    
    # 8.2 Сравнение конфигураций (таблица)
    stand_comparison_table: Optional[str] = Field(None, description="Таблица сравнения конфигураций (Система|Параметр|Значение на контуре|Значение на продуктивной среде)")
    
    # Раздел 9: Стратегия тестирования
    # 9.1 Описание планируемых тестов
    planned_tests_intro: Optional[str] = Field(None, description="Вводный текст к описанию планируемых тестов")
    planned_tests_table: Optional[str] = Field(None, description="Таблица планируемых тестов (№|Тест|Длительность теста|Описание теста)")
    planned_tests_note: Optional[str] = Field(None, description="Примечание о горизонтальной масштабируемости")
    
    # 9.2 Условия завершения НТ
    completion_conditions: Optional[str] = Field(None, description="Условия завершения НТ (маркированный список)")
    
    # Раздел 10: Наполнение БД
    database_preparation_text: Optional[str] = Field(None, description="Текст наполнения БД")
    database_preparation_table: Optional[str] = Field(None, description="Таблица требований к объемам данных (Схема.Таблица|Текущее кол-во строк|Прогноз роста в день)")
    
    # Раздел 11: Моделирование нагрузки
    # 11.1 Общие принципы моделирования нагрузки
    load_modeling_principles: Optional[str] = Field(None, description="Общие принципы моделирования нагрузки")
    
    # 11.2 Профили нагрузки
    load_profiles_intro: Optional[str] = Field(None, description="Вводный текст к профилям нагрузки")
    load_profiles_table: Optional[str] = Field(None, description="Таблица профилей нагрузки (Название страниц|Интенсивность нагрузки)")
    
    # 11.3 Сценарии использования
    use_scenarios_intro: Optional[str] = Field(None, description="Вводный текст к сценариям использования")
    use_scenarios_table: Optional[str] = Field(None, description="Таблица сценариев использования (Шаги|Интенсивность нагрузки)")
    
    # 11.4 Описание работы эмуляторов
    emulators_description: Optional[str] = Field(None, description="Описание работы эмуляторов")
    
    # Раздел 12: Мониторинг
    monitoring_intro: Optional[str] = Field(None, description="Вводный текст к разделу мониторинга")
    
    # 12.1 Описание средств мониторинга
    monitoring_tools_intro: Optional[str] = Field(None, description="Вводный текст к средствам мониторинга")
    monitoring_tools_table: Optional[str] = Field(None, description="Таблица средств мониторинга (Наименование|Роль|Эндпоинт (URI))")
    monitoring_tools_note: Optional[str] = Field(None, description="Примечания о мониторинге")
    
    # 12.2 Описание метрик мониторинга
    # 12.2.1 Мониторинг системных ресурсов
    system_resources_intro: Optional[str] = Field(None, description="Вводный текст к мониторингу системных ресурсов")
    system_resources_table: Optional[str] = Field(None, description="Таблица метрик системных ресурсов (№|Тип метрики|Способ снятия|Способ получения|Визуализация)")
    
    # 12.2.2 Мониторинг бизнес-метрик
    business_metrics_intro: Optional[str] = Field(None, description="Вводный текст к мониторингу бизнес-метрик")
    business_metrics_table: Optional[str] = Field(None, description="Таблица бизнес-метрик (Бизнес-метрика|Единица измерения)")
    
    # Раздел 13: Требования к Заказчику
    customer_requirements_intro: Optional[str] = Field(None, description="Вводный текст к требованиям к Заказчику")
    customer_requirements_list: Optional[str] = Field(None, description="Список требований к Заказчику (нумерованный список)")
    
    # Раздел 14: Материалы, подлежащие сдаче
    deliverables_intro: Optional[str] = Field(None, description="Вводный текст к материалам")
    deliverables_table: Optional[str] = Field(None, description="Таблица материалов (Документ|Подготавливается в результате деятельности)")
    
    # Раздел 15: Контакты
    contacts_table: Optional[str] = Field(None, description="Таблица контактов (п/п|ФИО|Сфера ответственности|Контакты)")
    
    # Пользовательские блоки (динамические)
    custom_sections: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Список пользовательских блоков. Каждый блок: {'id': str, 'title': str, 'position': int, 'text': str, 'table': str, 'list': str}"
    )
    
    # Confluence
    confluence_space: str = Field(..., description="Space key в Confluence")
    confluence_parent_id: Optional[int] = Field(None, description="Parent page ID (опционально)")
    confluence_page_title: Optional[str] = Field(None, description="Заголовок страницы")


class MNTDocument(BaseModel):
    """Модель документа МНТ для API"""
    id: Optional[int] = None
    title: str
    project: str
    author: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: MNTStatus = MNTStatus.DRAFT
    data_json: Dict[str, Any]
    confluence_space: Optional[str] = None
    confluence_parent_id: Optional[int] = None
    confluence_page_id: Optional[int] = None
    confluence_page_url: Optional[str] = None
    last_publish_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    class Config:
        from_attributes = True


class MNTCreateRequest(BaseModel):
    """Запрос на создание МНТ"""
    data: MNTData


class MNTUpdateRequest(BaseModel):
    """Запрос на обновление МНТ"""
    data: MNTData


class MNTListResponse(BaseModel):
    """Ответ со списком МНТ"""
    documents: List[MNTDocument]
    total: int
