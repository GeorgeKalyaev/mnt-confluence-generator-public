"""Модуль для отслеживания изменений полей МНТ"""
from typing import Dict, Any, List, Tuple, Optional
from app.logger import logger


def compare_document_fields(old_doc: Dict[str, Any], new_doc: Dict[str, Any]) -> List[Tuple[str, str, Any, Any]]:
    """
    Сравнивает два документа и возвращает список измененных полей.
    
    Args:
        old_doc: Старый документ
        new_doc: Новый документ
    
    Returns:
        Список кортежей: [(field_name, field_path, old_value, new_value), ...]
    """
    changes = []
    
    # Основные поля документа
    main_fields = ["title", "project", "author"]
    for field in main_fields:
        old_value = old_doc.get(field, "")
        new_value = new_doc.get(field, "")
        if old_value != new_value:
            changes.append((field, field, old_value, new_value))
    
    # Теги
    old_tags = sorted(old_doc.get("data_json", {}).get("tags", []))
    new_tags = sorted(new_doc.get("data_json", {}).get("tags", []))
    if old_tags != new_tags:
        changes.append(("tags", "data_json.tags", old_tags, new_tags))
    
    # Поля из data_json
    old_data = old_doc.get("data_json", {})
    new_data = new_doc.get("data_json", {})
    
    # Все поля data_json
    all_fields = set(list(old_data.keys()) + list(new_data.keys()))
    
    for field in all_fields:
        old_value = old_data.get(field, "")
        new_value = new_data.get(field, "")
        
        if old_value != new_value:
            field_path = f"data_json.{field}"
            changes.append((field, field_path, old_value, new_value))
    
    return changes


def get_field_display_name(field_name: str) -> str:
    """Получить отображаемое название поля"""
    display_names = {
        "title": "Название документа",
        "project": "Проект",
        "author": "Автор",
        "tags": "Теги",
        "introduction_text": "4. Введение",
        "goals_business": "5.1 Бизнес-цели",
        "goals_technical": "5.1 Технические цели",
        "tasks_nt": "5.2 Задачи НТ",
        "limitations_list": "6.1 Ограничения НТ",
        "risks_table": "6.2 Риски НТ",
        "object_general": "7.1 Общие сведения",
        "performance_requirements": "7.2 Требования к производительности",
        "component_architecture_text": "7.3.1 Компонентная архитектура",
        "test_stand_architecture_text": "8.1 Архитектура тестового стенда",
        "planned_tests_intro": "9.1 Описание планируемых тестов",
        "completion_conditions": "9.2 Условия завершения НТ",
        "database_preparation_text": "10. Наполнение БД (текст)",
        "load_modeling_principles": "11.1 Общие принципы моделирования нагрузки",
        "load_profiles_intro": "11.2 Профили нагрузки (введение)",
        "load_profiles_table": "11.2 Профили нагрузки (таблица)",
        "use_scenarios_intro": "11.3 Сценарии использования (введение)",
        "use_scenarios_table": "11.3 Сценарии использования (таблица)",
        "emulators_description": "11.4 Описание работы эмуляторов",
        "monitoring_intro": "12. Мониторинг (введение)",
        "monitoring_tools_intro": "12.1 Описание средств мониторинга (введение)",
        "monitoring_tools_table": "12.1 Описание средств мониторинга (таблица)",
        "system_resources_intro": "12.2.1 Мониторинг системных ресурсов (введение)",
        "system_resources_table": "12.2.1 Мониторинг системных ресурсов (таблица)",
        "business_metrics_intro": "12.2.2 Мониторинг бизнес-метрик (введение)",
        "business_metrics_table": "12.2.2 Мониторинг бизнес-метрик (таблица)",
        "customer_requirements_list": "13. Требования к Заказчику",
        "deliverables_intro": "14. Материалы, подлежащие сдаче (введение)",
        "deliverables_table": "14. Материалы, подлежащие сдаче (таблица 1)",
        "deliverables_working_docs_table": "14. Материалы, подлежащие сдаче (таблица 2)",
        "contacts_table": "15. Контакты",
        "history_changes_table": "1. История изменений",
        "approval_list_table": "2. Лист согласования",
        "abbreviations_table": "3.1 Сокращения",
        "terminology_table": "3.2 Терминология",
        "stand_comparison_table": "8.2 Сравнение конфигураций",
        "planned_tests_table": "9.1 Описание планируемых тестов (таблица)",
        "database_preparation_table": "10. Наполнение БД (таблица)",
    }
    
    return display_names.get(field_name, field_name)
