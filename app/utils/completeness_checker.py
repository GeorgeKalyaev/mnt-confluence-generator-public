"""Модуль для проверки полноты заполнения МНТ документа"""
from typing import Dict, List, Tuple, Any
import json


def check_section_completeness(data: Dict[str, Any], section_id: str, section_name: str) -> Tuple[bool, str]:
    """
    Проверяет заполненность конкретного раздела МНТ.
    
    Returns:
        Tuple[bool, str]: (заполнен ли раздел, описание проблемы если не заполнен)
    """
    if section_id == "section-header":  # Заголовок документа
        project_name = data.get("project_name", "").strip()
        organization_name = data.get("organization_name", "").strip()
        system_version = data.get("system_version", "").strip()
        author = data.get("author", "").strip()
        
        if not project_name or len(project_name) < 2:
            return False, "Название проекта не заполнено"
        if not organization_name or len(organization_name) < 2:
            return False, "Название компании не заполнено"
        if not system_version or len(system_version) < 1:
            return False, "Версия системы не заполнена"
        if not author or len(author) < 2:
            return False, "Автор не указан"
        return True, ""
    
    elif section_id == "section-1":  # История изменений
        history_table = data.get("history_changes_table", "").strip()
        if not history_table or history_table.count("\n") < 1:
            return False, "Таблица истории изменений пуста"
        return True, ""
    
    elif section_id == "section-2":  # Лист согласования
        approval_table = data.get("approval_list_table", "").strip()
        if not approval_table or approval_table.count("\n") < 1:
            return False, "Таблица листа согласования пуста"
        return True, ""
    
    elif section_id == "section-3":  # Сокращения и терминология
        abbreviations = data.get("abbreviations_table", "").strip()
        terminology = data.get("terminology_table", "").strip()
        if not abbreviations or abbreviations.count("\n") < 1:
            return False, "Таблица сокращений не заполнена"
        if not terminology or terminology.count("\n") < 1:
            return False, "Таблица терминологии не заполнена"
        return True, ""
    
    elif section_id == "section-4":  # Введение
        intro = data.get("introduction_text", "").strip()
        if not intro or len(intro) < 10:
            return False, "Текст введения слишком короткий или отсутствует"
        return True, ""
    
    elif section_id == "section-5":  # Цели и задачи НТ
        goals_business = data.get("goals_business", "").strip()
        goals_technical = data.get("goals_technical", "").strip()
        tasks_nt = data.get("tasks_nt", "").strip()
        
        if not goals_business or len(goals_business) < 10:
            return False, "Бизнес-цели не заполнены"
        if not goals_technical or len(goals_technical) < 10:
            return False, "Технические цели не заполнены"
        if not tasks_nt or len(tasks_nt) < 10:
            return False, "Задачи НТ не заполнены"
        return True, ""
    
    elif section_id == "section-6":  # Ограничения и риски НТ
        limitations = data.get("limitations_list", "").strip()
        risks_table = data.get("risks_table", "").strip()
        
        if not limitations or len(limitations) < 10:
            return False, "Список ограничений не заполнен"
        if not risks_table or risks_table.count("\n") < 1:
            return False, "Таблица рисков не заполнена"
        return True, ""
    
    elif section_id == "section-7":  # Объект НТ
        object_general = data.get("object_general", "").strip()
        performance = data.get("performance_requirements", "").strip()
        component_arch = data.get("component_architecture_text", "").strip()
        
        if not object_general or len(object_general) < 10:
            return False, "Общие сведения об объекте не заполнены"
        if not performance or len(performance) < 10:
            return False, "Требования к производительности не заполнены"
        if not component_arch or len(component_arch) < 10:
            return False, "Компонентная архитектура не заполнена"
        return True, ""
    
    elif section_id == "section-8":  # Тестовый и промышленный стенды
        test_stand = data.get("test_stand_architecture_text", "").strip()
        stand_comparison = data.get("stand_comparison_table", "").strip()
        
        if not test_stand or len(test_stand) < 10:
            return False, "Архитектура тестового стенда не заполнена"
        # stand_comparison может быть пустым (опционально)
        return True, ""
    
    elif section_id == "section-9":  # Стратегия тестирования
        planned_tests_intro = data.get("planned_tests_intro", "").strip()
        planned_tests_table = data.get("planned_tests_table", "").strip()
        completion = data.get("completion_conditions", "").strip()
        
        if not planned_tests_intro or len(planned_tests_intro) < 10:
            return False, "Введение к планируемым тестам не заполнено"
        if not planned_tests_table or planned_tests_table.count("\n") < 1:
            return False, "Таблица планируемых тестов не заполнена"
        if not completion or len(completion) < 10:
            return False, "Условия завершения НТ не заполнены"
        return True, ""
    
    elif section_id == "section-10":  # Наполнение БД
        db_text = data.get("database_preparation_text", "").strip()
        db_table = data.get("database_preparation_table", "").strip()
        
        if not db_text or len(db_text) < 10:
            return False, "Текст о наполнении БД не заполнен"
        if not db_table or db_table.count("\n") < 1:
            return False, "Таблица наполнения БД не заполнена"
        return True, ""
    
    elif section_id == "section-11":  # Моделирование нагрузки
        load_principles = data.get("load_modeling_principles", "").strip()
        load_profiles_intro = data.get("load_profiles_intro", "").strip()
        load_profiles_table = data.get("load_profiles_table", "").strip()
        use_scenarios_intro = data.get("use_scenarios_intro", "").strip()
        use_scenarios_table = data.get("use_scenarios_table", "").strip()
        emulators = data.get("emulators_description", "").strip()
        
        if not load_principles or len(load_principles) < 10:
            return False, "Принципы моделирования нагрузки не заполнены"
        if not load_profiles_intro or len(load_profiles_intro) < 10:
            return False, "Введение к профилям нагрузки не заполнено"
        if not load_profiles_table or load_profiles_table.count("\n") < 1:
            return False, "Таблица профилей нагрузки не заполнена"
        if not use_scenarios_intro or len(use_scenarios_intro) < 10:
            return False, "Введение к сценариям использования не заполнено"
        if not use_scenarios_table or use_scenarios_table.count("\n") < 1:
            return False, "Таблица сценариев использования не заполнена"
        if not emulators or len(emulators) < 10:
            return False, "Описание работы эмуляторов не заполнено"
        return True, ""
    
    elif section_id == "section-12":  # Мониторинг
        monitoring_intro = data.get("monitoring_intro", "").strip()
        monitoring_tools_intro = data.get("monitoring_tools_intro", "").strip()
        monitoring_tools_table = data.get("monitoring_tools_table", "").strip()
        system_resources_intro = data.get("system_resources_intro", "").strip()
        system_resources_table = data.get("system_resources_table", "").strip()
        business_metrics_intro = data.get("business_metrics_intro", "").strip()
        business_metrics_table = data.get("business_metrics_table", "").strip()
        
        if not monitoring_intro or len(monitoring_intro) < 10:
            return False, "Введение к мониторингу не заполнено"
        if not monitoring_tools_intro or len(monitoring_tools_intro) < 10:
            return False, "Введение к средствам мониторинга не заполнено"
        if not monitoring_tools_table or monitoring_tools_table.count("\n") < 1:
            return False, "Таблица средств мониторинга не заполнена"
        if not system_resources_intro or len(system_resources_intro) < 10:
            return False, "Введение к мониторингу системных ресурсов не заполнено"
        if not system_resources_table or system_resources_table.count("\n") < 1:
            return False, "Таблица мониторинга системных ресурсов не заполнена"
        if not business_metrics_intro or len(business_metrics_intro) < 10:
            return False, "Введение к мониторингу бизнес-метрик не заполнено"
        if not business_metrics_table or business_metrics_table.count("\n") < 1:
            return False, "Таблица мониторинга бизнес-метрик не заполнена"
        return True, ""
    
    elif section_id == "section-13":  # Требования к Заказчику
        customer_req = data.get("customer_requirements_list", "").strip()
        if not customer_req or len(customer_req) < 10:
            return False, "Требования к Заказчику не заполнены"
        return True, ""
    
    elif section_id == "section-14":  # Материалы, подлежащие сдаче
        deliverables_intro = data.get("deliverables_intro", "").strip()
        deliverables_table = data.get("deliverables_table", "").strip()
        deliverables_working_docs = data.get("deliverables_working_docs_table", "").strip()
        
        if not deliverables_intro or len(deliverables_intro) < 10:
            return False, "Введение к материалам не заполнено"
        if not deliverables_table or deliverables_table.count("\n") < 1:
            return False, "Таблица материалов не заполнена"
        if not deliverables_working_docs or deliverables_working_docs.count("\n") < 1:
            return False, "Таблица рабочих документов не заполнена"
        return True, ""
    
    elif section_id == "section-15":  # Контакты
        contacts_table = data.get("contacts_table", "").strip()
        if not contacts_table or contacts_table.count("\n") < 1:
            return False, "Таблица контактов не заполнена"
        return True, ""
    
    elif section_id == "section-tags":  # Теги
        # Теги - опциональное поле, но для индикатора проверяем заполнение
        tags = data.get("tags", "").strip()
        if not tags or len(tags) < 2:
            return False, "Теги не заполнены (опционально)"
        return True, ""
    
    elif section_id == "section-confluence":  # Публикация в Confluence
        # Публикация в Confluence - проверяем заполнение confluence_space
        # confluence_space имеет значение по умолчанию "TEST" в форме
        # confluence_parent_id - опциональное поле
        confluence_space = data.get("confluence_space", "").strip()
        if not confluence_space or len(confluence_space) < 1:
            return False, "Space Key не указан"
        # Если указан хотя бы space, считаем раздел заполненным
        return True, ""
    
    return True, ""  # Неизвестный раздел считаем заполненным


def check_document_completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Проверяет полноту заполнения всего документа МНТ.
    
    Returns:
        Dict с информацией о полноте:
        {
            "total_sections": int,
            "filled_sections": int,
            "completion_percentage": float,
            "sections": [
                {
                    "id": str,
                    "name": str,
                    "filled": bool,
                    "issue": str
                }
            ]
        }
    """
    sections = [
        ("section-header", "Заголовок документа"),
        ("section-1", "1. История изменений"),
        ("section-2", "2. Лист согласования"),
        ("section-3", "3. Сокращения и терминология"),
        ("section-4", "4. Введение"),
        ("section-5", "5. Цели и задачи НТ"),
        ("section-6", "6. Ограничения и риски НТ"),
        ("section-7", "7. Объект НТ"),
        ("section-8", "8. Тестовый и промышленный стенды"),
        ("section-9", "9. Стратегия тестирования"),
        ("section-10", "10. Наполнение БД"),
        ("section-11", "11. Моделирование нагрузки"),
        ("section-12", "12. Мониторинг"),
        ("section-13", "13. Требования к Заказчику"),
        ("section-14", "14. Материалы, подлежащие сдаче"),
        ("section-15", "15. Контакты"),
        ("section-tags", "Теги"),
        ("section-confluence", "Публикация в Confluence"),
    ]
    
    section_results = []
    filled_count = 0
    
    for section_id, section_name in sections:
        filled, issue = check_section_completeness(data, section_id, section_name)
        section_results.append({
            "id": section_id,
            "name": section_name,
            "filled": filled,
            "issue": issue
        })
        if filled:
            filled_count += 1
    
    total = len(sections)
    completion_percentage = (filled_count / total * 100) if total > 0 else 0
    
    return {
        "total_sections": total,
        "filled_sections": filled_count,
        "completion_percentage": round(completion_percentage, 1),
        "sections": section_results
    }
