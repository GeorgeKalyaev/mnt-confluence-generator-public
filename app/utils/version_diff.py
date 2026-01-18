"""Модуль для сравнения версий МНТ документов"""
from typing import Dict, Any, List, Tuple, Optional
import json
from difflib import unified_diff, SequenceMatcher


def compare_versions(version1: Dict[str, Any], version2: Dict[str, Any]) -> Dict[str, Any]:
    """Сравнение двух версий МНТ документа
    
    Args:
        version1: Старая версия (dict с данными МНТ)
        version2: Новая версия (dict с данными МНТ)
    
    Returns:
        Dict с результатами сравнения:
        {
            'fields_changed': List[Dict],  # Список измененных полей
            'tables_changed': List[Dict],  # Список измененных таблиц
            'metadata_changed': Dict,      # Изменения в метаданных (title, project, author, tags)
            'summary': Dict                # Общая статистика изменений
        }
    """
    data1 = version1.get('data_json', {}) if isinstance(version1, dict) else version1
    data2 = version2.get('data_json', {}) if isinstance(version2, dict) else version2
    
    # Если переданы полные объекты версий, извлекаем data_json
    if 'data_json' in version1:
        metadata1 = {
            'title': version1.get('title', ''),
            'project': version1.get('project', ''),
            'author': version1.get('author', ''),
            'tags': data1.get('tags', [])
        }
    else:
        metadata1 = {
            'title': '',
            'project': '',
            'author': '',
            'tags': data1.get('tags', [])
        }
    
    if 'data_json' in version2:
        metadata2 = {
            'title': version2.get('title', ''),
            'project': version2.get('project', ''),
            'author': version2.get('author', ''),
            'tags': data2.get('tags', [])
        }
    else:
        metadata2 = {
            'title': '',
            'project': '',
            'author': '',
            'tags': data2.get('tags', [])
        }
    
    # Сравниваем метаданные
    metadata_changes = compare_metadata(metadata1, metadata2)
    
    # Сравниваем текстовые поля
    text_fields = [
        'introduction_text', 'goals_business', 'goals_technical', 'tasks_nt',
        'limitations_list', 'object_general', 'performance_requirements',
        'component_architecture_text', 'information_architecture_text',
        'test_stand_architecture_text', 'methodology_text',
        'load_modeling_principles', 'load_profiles_intro', 'use_scenarios_intro',
        'emulators_description', 'monitoring_intro', 'monitoring_tools_intro',
        'monitoring_tools_note', 'system_resources_intro', 'business_metrics_intro',
        'customer_requirements_list', 'deliverables_intro',
        'database_preparation_text'
    ]
    
    fields_changed = []
    for field in text_fields:
        val1 = data1.get(field, '') or ''
        val2 = data2.get(field, '') or ''
        if val1 != val2:
            diff_result = compare_text_fields(field, val1, val2)
            if diff_result:
                fields_changed.append(diff_result)
    
    # Сравниваем таблицы
    table_fields = [
        'history_changes_table', 'approval_list_table', 'abbreviations_table',
        'terminology_table', 'risks_table', 'stand_comparison_table',
        'planned_tests_table', 'database_preparation_table',
        'load_profiles_table', 'use_scenarios_table',
        'monitoring_tools_table', 'system_resources_table', 'business_metrics_table',
        'deliverables_table', 'deliverables_working_docs_table', 'contacts_table'
    ]
    
    tables_changed = []
    for field in table_fields:
        val1 = data1.get(field, '') or ''
        val2 = data2.get(field, '') or ''
        if val1 != val2:
            diff_result = compare_tables(field, val1, val2)
            if diff_result:
                tables_changed.append(diff_result)
    
    # Статистика
    summary = {
        'fields_changed_count': len(fields_changed),
        'tables_changed_count': len(tables_changed),
        'metadata_changed_count': len([k for k, v in metadata_changes.items() if v['changed']]),
        'total_changes': len(fields_changed) + len(tables_changed) + len([k for k, v in metadata_changes.items() if v['changed']])
    }
    
    return {
        'fields_changed': fields_changed,
        'tables_changed': tables_changed,
        'metadata_changed': metadata_changes,
        'summary': summary
    }


def compare_metadata(metadata1: Dict, metadata2: Dict) -> Dict[str, Dict]:
    """Сравнение метаданных (title, project, author, tags)"""
    changes = {}
    
    for key in ['title', 'project', 'author']:
        val1 = metadata1.get(key, '')
        val2 = metadata2.get(key, '')
        if val1 != val2:
            changes[key] = {
                'changed': True,
                'old_value': val1,
                'new_value': val2,
                'diff': compare_text_fields(key, val1, val2)
            }
        else:
            changes[key] = {'changed': False}
    
    # Сравниваем теги
    tags1 = set(metadata1.get('tags', []) or [])
    tags2 = set(metadata2.get('tags', []) or [])
    if tags1 != tags2:
        added = list(tags2 - tags1)
        removed = list(tags1 - tags2)
        changes['tags'] = {
            'changed': True,
            'old_value': list(tags1),
            'new_value': list(tags2),
            'added': added,
            'removed': removed
        }
    else:
        changes['tags'] = {'changed': False}
    
    return changes


def compare_text_fields(field_name: str, text1: str, text2: str) -> Optional[Dict[str, Any]]:
    """Сравнение текстовых полей с генерацией diff"""
    if text1 == text2:
        return None
    
    lines1 = text1.splitlines(keepends=True) if text1 else ['']
    lines2 = text2.splitlines(keepends=True) if text2 else ['']
    
    # Генерируем unified diff
    diff_lines = list(unified_diff(
        lines1,
        lines2,
        fromfile=f'{field_name} (старая версия)',
        tofile=f'{field_name} (новая версия)',
        lineterm=''
    ))
    
    # Также генерируем side-by-side представление
    side_by_side = generate_side_by_side(lines1, lines2)
    
    return {
        'field_name': field_name,
        'field_label': get_field_label(field_name),
        'old_value': text1,
        'new_value': text2,
        'unified_diff': diff_lines,
        'side_by_side': side_by_side,
        'changed': True
    }


def compare_tables(field_name: str, table1: str, table2: str) -> Optional[Dict[str, Any]]:
    """Сравнение таблиц с детальным анализом изменений"""
    if table1 == table2:
        return None
    
    # Парсим таблицы
    rows1 = parse_table(table1)
    rows2 = parse_table(table2)
    
    # Сравниваем построчно
    table_diff = compare_table_rows(rows1, rows2)
    
    return {
        'field_name': field_name,
        'field_label': get_field_label(field_name),
        'old_value': table1,
        'new_value': table2,
        'old_rows': rows1,
        'new_rows': rows2,
        'diff': table_diff,
        'changed': True
    }


def parse_table(table_text: str) -> List[List[str]]:
    """Парсит таблицу из текстового формата (строки через \n, колонки через |)"""
    if not table_text:
        return []
    
    lines = [line.strip() for line in table_text.split('\n') if line.strip()]
    rows = []
    
    for line in lines:
        columns = [col.strip() for col in line.split('|')]
        rows.append(columns)
    
    return rows


def compare_table_rows(rows1: List[List[str]], rows2: List[List[str]]) -> Dict[str, Any]:
    """Сравнивает строки двух таблиц построчно"""
    diff_result = {
        'added_rows': [],
        'removed_rows': [],
        'modified_rows': [],
        'unchanged_rows': []
    }
    
    # Создаем словарь строк для быстрого поиска
    # Используем первую колонку (или несколько колонок) как ключ
    rows1_dict = {tuple(row): row for row in rows1}
    rows2_dict = {tuple(row): row for row in rows2}
    
    # Находим добавленные строки
    for row_key, row in rows2_dict.items():
        if row_key not in rows1_dict:
            diff_result['added_rows'].append({
                'row': row,
                'row_number': rows2.index(row) + 1
            })
    
    # Находим удаленные строки
    for row_key, row in rows1_dict.items():
        if row_key not in rows2_dict:
            diff_result['removed_rows'].append({
                'row': row,
                'row_number': rows1.index(row) + 1
            })
    
    # Находим измененные строки (строки с одинаковым ключом, но разным содержимым)
    # Для этого сравниваем строки по первой колонке
    rows1_by_first_col = {}
    rows2_by_first_col = {}
    
    for i, row in enumerate(rows1):
        if row:
            key = row[0]
            rows1_by_first_col[key] = (row, i + 1)
    
    for i, row in enumerate(rows2):
        if row:
            key = row[0]
            rows2_by_first_col[key] = (row, i + 1)
    
    # Сравниваем строки с одинаковым первым столбцом
    for key in set(rows1_by_first_col.keys()) & set(rows2_by_first_col.keys()):
        row1, num1 = rows1_by_first_col[key]
        row2, num2 = rows2_by_first_col[key]
        
        if row1 != row2:
            # Находим измененные ячейки
            cell_changes = []
            max_cols = max(len(row1), len(row2))
            for col_idx in range(max_cols):
                val1 = row1[col_idx] if col_idx < len(row1) else ''
                val2 = row2[col_idx] if col_idx < len(row2) else ''
                if val1 != val2:
                    cell_changes.append({
                        'column_index': col_idx,
                        'old_value': val1,
                        'new_value': val2
                    })
            
            diff_result['modified_rows'].append({
                'row_key': key,
                'old_row': row1,
                'new_row': row2,
                'old_row_number': num1,
                'new_row_number': num2,
                'cell_changes': cell_changes
            })
        else:
            diff_result['unchanged_rows'].append({
                'row': row1,
                'row_number': num1
            })
    
    return diff_result


def generate_side_by_side(lines1: List[str], lines2: List[str]) -> List[Dict[str, Any]]:
    """Генерирует side-by-side представление для сравнения текста"""
    max_lines = max(len(lines1), len(lines2))
    side_by_side = []
    
    for i in range(max_lines):
        line1 = lines1[i] if i < len(lines1) else ''
        line2 = lines2[i] if i < len(lines2) else ''
        
        line_type = 'unchanged'
        if line1 != line2:
            if i >= len(lines1):
                line_type = 'added'
            elif i >= len(lines2):
                line_type = 'removed'
            else:
                line_type = 'modified'
        
        side_by_side.append({
            'line_number': i + 1,
            'old_line': line1.rstrip('\n\r'),
            'new_line': line2.rstrip('\n\r'),
            'type': line_type
        })
    
    return side_by_side


def get_field_label(field_name: str) -> str:
    """Получает человекочитаемое название поля"""
    labels = {
        'introduction_text': '4. Введение',
        'goals_business': '5.1 Бизнес-цели',
        'goals_technical': '5.1 Технические цели',
        'tasks_nt': '5.2 Задачи НТ',
        'limitations_list': '6.1 Ограничения НТ',
        'object_general': '7.1 Общие сведения',
        'performance_requirements': '7.2 Требования к производительности',
        'component_architecture_text': '7.3.1 Компонентная архитектура',
        'information_architecture_text': '7.3.2 Информационная архитектура',
        'test_stand_architecture_text': '8.1 Архитектура тестового стенда',
        'stand_comparison_table': '8.2 Сравнение конфигураций',
        'planned_tests_table': '9.1 Описание планируемых тестов',
        'database_preparation_table': '10. Наполнение БД',
        'load_profiles_table': '11.2 Профили нагрузки',
        'use_scenarios_table': '11.3 Сценарии использования',
        'emulators_description': '11.4 Описание работы эмуляторов',
        'monitoring_tools_table': '12.1 Описание средств мониторинга',
        'system_resources_table': '12.2.1 Мониторинг системных ресурсов',
        'business_metrics_table': '12.2.2 Мониторинг бизнес-метрик',
        'customer_requirements_list': '13. Требования к Заказчику',
        'deliverables_table': '14. Материалы, подлежащие сдаче',
        'contacts_table': '15. Контакты',
        'history_changes_table': '1. История изменений',
        'approval_list_table': '2. Лист согласования',
        'abbreviations_table': '3.1 Сокращения',
        'terminology_table': '3.2 Терминология',
        'risks_table': '6.2 Риски НТ'
    }
    
    return labels.get(field_name, field_name)
