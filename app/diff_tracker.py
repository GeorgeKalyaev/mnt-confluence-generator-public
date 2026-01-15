"""Модуль для отслеживания изменений в МНТ данных"""
from typing import Dict, List, Any, Optional
import json


def compare_values(old_value: Any, new_value: Any) -> Optional[Dict[str, Any]]:
    """Сравнивает два значения и возвращает информацию об изменении"""
    # Обработка None
    if old_value is None and new_value is None:
        return None
    if old_value is None:
        return {"type": "added", "old": None, "new": new_value}
    if new_value is None:
        return {"type": "removed", "old": old_value, "new": None}
    
    # Сравнение строк
    if isinstance(old_value, str) and isinstance(new_value, str):
        if old_value.strip() != new_value.strip():
            return {"type": "changed", "old": old_value, "new": new_value}
    
    # Сравнение чисел
    elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
        if old_value != new_value:
            return {"type": "changed", "old": old_value, "new": new_value}
    
    # Сравнение списков
    elif isinstance(old_value, list) and isinstance(new_value, list):
        if json.dumps(old_value, ensure_ascii=False, sort_keys=True) != json.dumps(new_value, ensure_ascii=False, sort_keys=True):
            return {"type": "changed", "old": old_value, "new": new_value}
    
    # Сравнение других типов через JSON
    else:
        old_str = json.dumps(old_value, ensure_ascii=False, sort_keys=True)
        new_str = json.dumps(new_value, ensure_ascii=False, sort_keys=True)
        if old_str != new_str:
            return {"type": "changed", "old": old_value, "new": new_value}
    
    return None


def compare_mnt_data(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Сравнивает две версии данных МНТ и возвращает список изменений"""
    changes = []
    
    # Получаем все уникальные ключи из обоих словарей
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    # Маппинг ключей на читаемые названия полей
    field_names = {
        "title": "Название МНТ",
        "project_name": "Название проекта",
        "author": "Автор",
        "organization_name": "Название организации",
        "system_version": "Версия системы",
        "introduction_text": "Текст введения",
        "goals_business": "Бизнес-цели НТ",
        "goals_technical": "Технические цели НТ",
        "tasks_nt": "Задачи НТ",
        "limitations_list": "Ограничения НТ",
        "risks_table": "Таблица рисков",
        "object_general": "Общие сведения об объекте НТ",
        "performance_requirements": "Требования к производительности",
        "component_architecture_text": "Описание компонентной архитектуры",
        "component_architecture_image": "Изображение компонентной архитектуры",
        "information_architecture_image": "Изображение информационной архитектуры",
        "test_stand_architecture_text": "Архитектура тестового стенда",
        "stand_comparison_table": "Сравнение конфигураций",
        "planned_tests_table": "Таблица планируемых тестов",
        "completion_conditions": "Условия завершения НТ",
        "database_preparation_text": "Текст о наполнении БД",
        "database_preparation_table": "Таблица наполнения БД",
        "load_modeling_principles": "Принципы моделирования нагрузки",
        "load_profiles_table": "Профили нагрузки",
        "use_scenarios_table": "Сценарии использования",
        "emulators_description": "Описание работы эмуляторов",
        "monitoring_tools_table": "Таблица средств мониторинга",
        "monitoring_intro": "Введение в мониторинг",
        "system_resources_table": "Таблица системных метрик",
        "business_metrics_table": "Таблица бизнес-метрик",
        "customer_requirements_intro": "Введение в требования к заказчику",
        "customer_requirements_list": "Список требований к заказчику",
        "deliverables_table": "Таблица материалов для сдачи",
        "contacts_table": "Таблица контактов",
        "history_changes_table": "Таблица истории изменений",
        "approval_list_table": "Лист согласования",
        "abbreviations_table": "Таблица сокращений",
        "terminology_table": "Таблица терминологии",
        "tags": "Теги",
        "confluence_space": "Space в Confluence",
        "confluence_parent_id": "Родительская страница в Confluence",
    }
    
    for key in sorted(all_keys):
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        change = compare_values(old_value, new_value)
        if change:
            field_name = field_names.get(key, key)
            change_info = {
                "field": key,
                "field_name": field_name,
                **change
            }
            changes.append(change_info)
    
    return changes


def format_change_for_display(change: Dict[str, Any]) -> str:
    """Форматирует изменение для отображения в UI"""
    field_name = change.get("field_name", change.get("field", "Неизвестное поле"))
    change_type = change.get("type")
    
    if change_type == "added":
        new_val = change.get("new", "")
        if isinstance(new_val, str):
            if len(new_val) > 100:
                new_val = new_val[:100] + "..."
            return f"Добавлено: {field_name} = '{new_val}'"
        elif isinstance(new_val, list):
            return f"Добавлено: {field_name} ({len(new_val)} элементов)"
        else:
            return f"Добавлено: {field_name}"
    
    elif change_type == "removed":
        old_val = change.get("old", "")
        if isinstance(old_val, str):
            if len(old_val) > 100:
                old_val = old_val[:100] + "..."
            return f"Удалено: {field_name} = '{old_val}'"
        elif isinstance(old_val, list):
            return f"Удалено: {field_name} ({len(old_val)} элементов)"
        else:
            return f"Удалено: {field_name}"
    
    elif change_type == "changed":
        old_val = change.get("old", "")
        new_val = change.get("new", "")
        
        # Для строк показываем первые 50 символов
        if isinstance(old_val, str) and isinstance(new_val, str):
            old_display = old_val[:50] + "..." if len(old_val) > 50 else old_val
            new_display = new_val[:50] + "..." if len(new_val) > 50 else new_val
            return f"Изменено: {field_name}\n  Было: '{old_display}'\n  Стало: '{new_display}'"
        # Для таблиц показываем количество строк
        elif isinstance(old_val, list) and isinstance(new_val, list):
            return f"Изменено: {field_name} (было {len(old_val)} строк, стало {len(new_val)} строк)"
        else:
            return f"Изменено: {field_name}"
    
    return f"Изменено: {field_name}"
