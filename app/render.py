"""Генерация контента для Confluence в Storage Format"""
from typing import Dict, Any, List, Tuple
import html
import re
from datetime import datetime


def escape_xml(text: str) -> str:
    """Экранирование XML символов"""
    if not text:
        return ""
    return html.escape(str(text))


def render_text_field(text: str) -> str:
    """Рендеринг текстового поля с разбиением на параграфы"""
    if not text:
        return ""
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if line:
            result.append(f'<p>{escape_xml(line)}</p>')
    return ''.join(result)


def render_list_field(text: str, ordered: bool = False) -> str:
    """Рендеринг списка (маркированного или нумерованного)"""
    if not text:
        return ""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return ""
    
    tag = 'ol' if ordered else 'ul'
    result = [f'<{tag}>']
    
    for line in lines:
        # Убираем нумерацию если есть (1., 2., и т.д.)
        if ordered:
            line = re.sub(r'^\d+\.\s*', '', line)
        # Убираем маркеры если есть (-, •, и т.д.)
        else:
            line = re.sub(r'^[-•*]\s*', '', line)
        result.append(f'<li>{escape_xml(line)}</li>')
    
    result.append(f'</{tag}>')
    return ''.join(result)


def render_table_from_text(text: str, table_num: int = None, caption: str = None) -> Tuple[str, int]:
    """Преобразование текста в HTML-таблицу (формат: столбцы через |)
    
    Returns:
        Tuple[table_html, next_table_num]
    """
    if not text:
        return "", table_num or 0
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return "", table_num or 0
    
    # Проверяем, есть ли разделитель |
    if '|' not in lines[0]:
        # Если нет разделителя - возвращаем как обычный текст
        return render_text_field(text), table_num or 0
    
    # Парсим как таблицу
    table_html = []
    
    # Добавляем заголовок таблицы если указан номер
    if table_num is not None and caption:
        table_html.append(f'<p><strong>Таблица {table_num} - {escape_xml(caption)}</strong></p>')
    elif table_num is not None:
        table_html.append(f'<p><strong>Таблица {table_num}</strong></p>')
    
    table_html.append('<table>')
    
    for i, line in enumerate(lines):
        columns = [col.strip() for col in line.split('|')]
        if i == 0:
            # Первая строка - заголовок
            table_html.append('<tr>')
            for col in columns:
                table_html.append(f'<th>{escape_xml(col)}</th>')
            table_html.append('</tr>')
        else:
            # Обычная строка
            table_html.append('<tr>')
            
            # Определяем термин (первая колонка)
            term = columns[0].strip() if len(columns) > 0 else ''
            is_max_performance = term.lower() in ['максимальная производительность', 'максимальнаяпроизводительность']
            
            for j, col in enumerate(columns):
                if j == 0:
                    # Колонка с термином
                    table_html.append(f'<td>{escape_xml(col.strip())}</td>')
                elif j == 1:
                    # Колонка с определением
                    definition = col.strip()
                    definition_html = escape_xml(definition)
                    
                    # Если термин "Максимальная производительность", добавляем изображение
                    if is_max_performance:
                        definition_html += f'<br/><ac:image><ri:attachment ri:filename="max_performance.png" /></ac:image>'
                    
                    table_html.append(f'<td>{definition_html}</td>')
                else:
                    # Остальные колонки
                    table_html.append(f'<td>{escape_xml(col.strip())}</td>')
            table_html.append('</tr>')
    
    table_html.append('</table>')
    next_table_num = (table_num or 0) + 1
    return ''.join(table_html), next_table_num


def render_image_macro(filename: str, figure_num: int = None, caption: str = None) -> Tuple[str, int]:
    """Генерация макроса изображения в Confluence Storage Format
    
    Returns:
        Tuple[image_html, next_figure_num]
    """
    result = []
    
    # Добавляем подпись рисунка если указан номер
    if figure_num is not None and caption:
        result.append(f'<p><strong>Рисунок {figure_num} {escape_xml(caption)}</strong></p>')
    elif figure_num is not None:
        result.append(f'<p><strong>Рисунок {figure_num}</strong></p>')
    
    result.append(f'<p><ac:image><ri:attachment ri:filename="{escape_xml(filename)}"/></ac:image></p>')
    
    next_figure_num = (figure_num or 0) + 1
    return ''.join(result), next_figure_num


def replace_table_references(text: str, table_refs: Dict[int, int]) -> str:
    """Замена ссылок на таблицы в тексте (например, "Таблица 5" на правильный номер)"""
    if not text:
        return text
    
    # Заменяем ссылки типа "Таблица 1", "Таблица 2" и т.д.
    for old_num, new_num in table_refs.items():
        # Ищем паттерны типа "Таблица N", "таблица N", "см. Таблица N"
        pattern = rf'\b([Тт]аблица|см\.\s*[Тт]аблица)\s+{old_num}\b'
        replacement = rf'\1 {new_num}'
        text = re.sub(pattern, replacement, text)
    
    return text


def generate_table_of_contents(sections: List[Tuple[str, int]]) -> str:
    """Генерация содержания на основе списка разделов
    
    Args:
        sections: Список кортежей (название_раздела, уровень_заголовка)
    """
    if not sections:
        return ""
    
    toc = ['<h1>Содержание</h1>', '<table>']
    
    section_num = 0
    sub_num_map = {}  # Для отслеживания номеров подразделов: {section_num: {'2': count, '3': {sub_num: count}}}
    
    for section_name, level in sections:
        if level == 1:  # H1 - основной раздел
            section_num += 1
            sub_num_map[section_num] = {'2': 0, '3': {}}
            toc.append(f'<tr><td>{section_num}</td><td>{escape_xml(section_name)}</td></tr>')
        elif level == 2:  # H2 - подраздел
            if section_num == 0:
                section_num = 1
                sub_num_map[section_num] = {'2': 0, '3': {}}
            sub_num_map[section_num]['2'] += 1
            sub_num = sub_num_map[section_num]['2']
            # Сбрасываем счетчик для уровня 3 при переходе к новому подразделу
            sub_num_map[section_num]['3'][sub_num] = 0
            toc.append(f'<tr><td>{section_num}.{sub_num}</td><td>{escape_xml(section_name)}</td></tr>')
        elif level == 3:  # H3 - под-подраздел
            if section_num == 0:
                section_num = 1
                sub_num_map[section_num] = {'2': 0, '3': {}}
            # Берем последний подраздел уровня 2
            sub_num = sub_num_map[section_num]['2']
            if sub_num == 0:
                sub_num = 1
                sub_num_map[section_num]['2'] = 1
            if sub_num not in sub_num_map[section_num]['3']:
                sub_num_map[section_num]['3'][sub_num] = 0
            sub_num_map[section_num]['3'][sub_num] += 1
            sub_sub_num = sub_num_map[section_num]['3'][sub_num]
            toc.append(f'<tr><td>{section_num}.{sub_num}.{sub_sub_num}</td><td>{escape_xml(section_name)}</td></tr>')
    
    toc.append('</table>')
    return ''.join(toc)


def render_mnt_to_confluence_storage(
    data: Dict[str, Any], 
    component_architecture_image: str = None,
    information_architecture_image: str = None,
    other_images: List[str] = None
) -> str:
    """Генерация контента МНТ в Confluence Storage Format согласно новой структуре
    
    Args:
        data: Данные МНТ
        component_architecture_image: Имя файла изображения компонентной архитектуры
        information_architecture_image: Имя файла изображения информационной архитектуры
        other_images: Список других изображений для вставки в конец
    """
    
    content_parts = []
    sections = []  # Для генерации содержания
    table_num = 1  # Счетчик таблиц
    figure_num = 1  # Счетчик рисунков
    table_refs = {}  # Маппинг старых номеров на новые (для замены ссылок)
    
    # Заголовок документа
    content_parts.append('<h1>Методика нагрузочного тестирования</h1>')
    if data.get("project_name"):
        content_parts.append(f'<p><strong>{escape_xml(data["project_name"])}</strong></p>')
    if data.get("organization_name"):
        content_parts.append(f'<p>{escape_xml(data["organization_name"])}</p>')
    if data.get("system_version"):
        content_parts.append(f'<p>Версия системы {escape_xml(data["system_version"])}</p>')
    
    # Раздел 1: История изменений
    if data.get("history_changes_table"):
        sections.append(("История изменений", 1))
        content_parts.append('<h1>1 История изменений</h1>')
        text = "История изменений документа представлена в таблице Таблица 1."
        text = replace_table_references(text, {1: table_num})
        content_parts.append(f'<p>{escape_xml(text)}</p>')
        table_html, table_num = render_table_from_text(
            data["history_changes_table"], 
            table_num=table_num,
            caption="История изменений документа"
        )
        content_parts.append(table_html)
    
    # Раздел 2: Лист согласования
    if data.get("approval_list_table"):
        sections.append(("Лист согласования", 1))
        content_parts.append('<h1>2 Лист согласования</h1>')
        content_parts.append('<p>Заполняется согласующими лицами со стороны заказчика.</p>')
        table_html, table_num = render_table_from_text(
            data["approval_list_table"],
            table_num=table_num,
            caption="Лист согласования"
        )
        content_parts.append(table_html)
    
    # Раздел 3: Сокращения и терминология
    if data.get("abbreviations_table") or data.get("terminology_table"):
        sections.append(("Сокращения и терминология", 1))
        content_parts.append('<h1>3 Сокращения и терминология</h1>')
        
        # 3.1 Сокращения
        if data.get("abbreviations_table"):
            sections.append(("Сокращения", 2))
            content_parts.append('<h2>3.1 Сокращения</h2>')
            text = "В таблице Таблица 3 приводятся используемые в документе список сокращений и их расшифровка."
            text = replace_table_references(text, {3: table_num})
            content_parts.append(f'<p>{escape_xml(text)}</p>')
            table_html, table_num = render_table_from_text(
                data["abbreviations_table"],
                table_num=table_num,
                caption="Список сокращений и их расшифровка"
            )
            content_parts.append(table_html)
        
        # 3.2 Терминология
        if data.get("terminology_table"):
            sections.append(("Терминология", 2))
            content_parts.append('<h2>3.2 Терминология</h2>')
            text = "В таблице Таблица 4 приводятся основные используемые в данном документе и в процессах нагрузочного тестирования термины."
            text = replace_table_references(text, {4: table_num})
            content_parts.append(f'<p>{escape_xml(text)}</p>')
            table_html, table_num = render_table_from_text(
                data["terminology_table"],
                table_num=table_num,
                caption="Основные используемые термины и их описание"
            )
            content_parts.append(table_html)
    
    # Раздел 4: Введение
    if data.get("introduction_text"):
        sections.append(("Введение", 1))
        content_parts.append('<h1>4 Введение</h1>')
        content_parts.append(render_text_field(data["introduction_text"]))
    
    # Раздел 5: Цели и задачи НТ
    if data.get("goals_business") or data.get("goals_technical") or data.get("tasks_nt"):
        sections.append(("Цели и задачи НТ", 1))
        content_parts.append('<h1>5 Цели и задачи НТ</h1>')
        
        # 5.1 Цели НТ
        if data.get("goals_business") or data.get("goals_technical"):
            sections.append(("Цели НТ", 2))
            content_parts.append('<h2>5.1 Цели НТ</h2>')
            content_parts.append('<p>Целями нагрузочного тестирования являются:</p>')
            if data.get("goals_business"):
                content_parts.append('<p><strong>Бизнес-цели:</strong></p>')
                content_parts.append(render_list_field(data["goals_business"], ordered=False))
            if data.get("goals_technical"):
                content_parts.append('<p><strong>Технические цели:</strong></p>')
                content_parts.append(render_list_field(data["goals_technical"], ordered=False))
        
        # 5.2 Задачи НТ
        if data.get("tasks_nt"):
            sections.append(("Задачи НТ", 2))
            content_parts.append('<h2>5.2 Задачи НТ</h2>')
            content_parts.append('<p>Для достижения целей нагрузочного тестирования необходимо выполнить ряд задач:</p>')
            content_parts.append(render_list_field(data["tasks_nt"], ordered=True))
    
    # Раздел 6: Ограничения и риски НТ
    if data.get("limitations_list") or data.get("risks_table"):
        sections.append(("Ограничения и риски НТ", 1))
        content_parts.append('<h1>6 Ограничения и риски НТ</h1>')
        
        # 6.1 Ограничения НТ
        if data.get("limitations_list"):
            sections.append(("Ограничения НТ", 2))
            content_parts.append('<h2>6.1 Ограничения НТ</h2>')
            content_parts.append(render_list_field(data["limitations_list"], ordered=True))
        
        # 6.2 Риски НТ
        if data.get("risks_table"):
            sections.append(("Риски НТ", 2))
            content_parts.append('<h2>6.2 Риски НТ</h2>')
            text = "Риски при проведении НТ и их влияние на его результат описаны в таблице 5."
            text = replace_table_references(text, {5: table_num})
            content_parts.append(f'<p>{escape_xml(text)}</p>')
            table_html, table_num = render_table_from_text(
                data["risks_table"],
                table_num=table_num,
                caption="Риски НТ"
            )
            content_parts.append(table_html)
    
    # Раздел 7: Объект НТ
    if data.get("object_general") or data.get("performance_requirements") or data.get("component_architecture_text") or component_architecture_image or information_architecture_image:
        sections.append(("Объект НТ", 1))
        content_parts.append('<h1>7 Объект НТ</h1>')
        
        # 7.1 Общие сведения
        if data.get("object_general"):
            sections.append(("Общие сведения", 2))
            content_parts.append('<h2>7.1 Общие сведения</h2>')
            content_parts.append(render_text_field(data["object_general"]))
        
        # 7.2 Требования к производительности
        if data.get("performance_requirements"):
            sections.append(("Требования к производительности", 2))
            content_parts.append('<h2>7.2 Требования к производительности</h2>')
            content_parts.append('<p>Для тестируемой системы «указываем название системы» Заказчиком были выдвинуты следующие нефункциональные требования к производительности:</p>')
            content_parts.append(render_list_field(data["performance_requirements"], ordered=False))
        
        # 7.3 Архитектура системы
        if data.get("component_architecture_text") or component_architecture_image or information_architecture_image:
            sections.append(("Архитектура системы", 2))
            content_parts.append('<h2>7.3 Архитектура системы</h2>')
            
            # 7.3.1 Компонентная архитектура
            if data.get("component_architecture_text") or component_architecture_image:
                sections.append(("Компонентная архитектура", 3))
                content_parts.append('<h3>7.3.1 Компонентная архитектура</h3>')
                if data.get("component_architecture_text"):
                    content_parts.append('<p>Компонентная архитектура состоит из следующих частей:</p>')
                    content_parts.append(render_list_field(data["component_architecture_text"], ordered=False))
                if component_architecture_image:
                    img_html, figure_num = render_image_macro(
                        component_architecture_image,
                        figure_num=figure_num,
                        caption="Компонентная архитектура"
                    )
                    content_parts.append(img_html)
            
            # 7.3.2 Информационная архитектура
            if information_architecture_image:
                sections.append(("Информационная архитектура", 3))
                content_parts.append('<h3>7.3.2 Информационная архитектура</h3>')
                img_html, figure_num = render_image_macro(
                    information_architecture_image,
                    figure_num=figure_num,
                    caption="Информационная архитектура"
                )
                content_parts.append(img_html)
    
    # Раздел 8: Тестовый и промышленный стенды
    if data.get("test_stand_architecture_text") or data.get("stand_comparison_table"):
        sections.append(("Тестовый и промышленный стенды", 1))
        content_parts.append('<h1>8 Тестовый и промышленный стенды</h1>')
        
        # 8.1 Архитектура тестового стенда
        if data.get("test_stand_architecture_text"):
            sections.append(("Архитектура тестового стенда", 2))
            content_parts.append('<h2>8.1 Архитектура тестового стенда</h2>')
            content_parts.append(render_text_field(data["test_stand_architecture_text"]))
        
        # 8.2 Сравнение конфигураций
        if data.get("stand_comparison_table"):
            sections.append(("Сравнение конфигураций промышленной среды и тестового стенда", 2))
            content_parts.append('<h2>8.2 Сравнение конфигураций промышленной среды и тестового стенда</h2>')
            text = "Сравнение продуктового и тестового стенда представлено см. Таблица 6."
            text = replace_table_references(text, {6: table_num})
            content_parts.append(f'<p>{escape_xml(text)}</p>')
            table_html, table_num = render_table_from_text(
                data["stand_comparison_table"],
                table_num=table_num,
                caption="Конфигурация серверов тестового (UAT) и продуктивного стендов. Сравнительная таблица"
            )
            content_parts.append(table_html)
    
    # Раздел 9: Стратегия тестирования
    if data.get("planned_tests_table") or data.get("completion_conditions"):
        sections.append(("Стратегия тестирования", 1))
        content_parts.append('<h1>9 Стратегия тестирования</h1>')
        
        # 9.1 Описание планируемых тестов
        if data.get("planned_tests_intro") or data.get("planned_tests_table"):
            sections.append(("Описание планируемых тестов", 2))
            content_parts.append('<h2>9.1 Описание планируемых тестов</h2>')
            if data.get("planned_tests_intro"):
                intro_text = data["planned_tests_intro"]
                intro_text = replace_table_references(intro_text, {7: table_num})
                content_parts.append(render_text_field(intro_text))
            if data.get("planned_tests_table"):
                table_html, table_num = render_table_from_text(
                    data["planned_tests_table"],
                    table_num=table_num,
                    caption="Перечень типов тестов"
                )
                content_parts.append(table_html)
            # Примечание planned_tests_note не добавляется в Confluence - это только напоминание в форме
        
        # 9.2 Условия завершения НТ
        if data.get("completion_conditions"):
            sections.append(("Условия завершения НТ", 2))
            content_parts.append('<h2>9.2 Условия завершения НТ</h2>')
            content_parts.append('<p>Критериями успешного завершения нагрузочного тестирования являются:</p>')
            content_parts.append(render_list_field(data["completion_conditions"], ordered=False))
    
    # Раздел 10: Наполнение БД
    if data.get("database_preparation_text") or data.get("database_preparation_table"):
        sections.append(("Наполнение БД", 1))
        content_parts.append('<h1>10 Наполнение БД</h1>')
        if data.get("database_preparation_text"):
            content_parts.append(render_text_field(data["database_preparation_text"]))
        if data.get("database_preparation_table"):
            text = "Требования к объемам данных представлены в Таблица 8."
            text = replace_table_references(text, {8: table_num})
            content_parts.append(f'<p>{escape_xml(text)}</p>')
            table_html, table_num = render_table_from_text(
                data["database_preparation_table"],
                table_num=table_num,
                caption="Требования к объемам данных"
            )
            content_parts.append(table_html)
    
    # Раздел 11: Моделирование нагрузки
    if data.get("load_modeling_principles") or data.get("load_profiles_table") or data.get("use_scenarios_table") or data.get("emulators_description"):
        sections.append(("Моделирование нагрузки", 1))
        content_parts.append('<h1>11 Моделирование нагрузки</h1>')
        
        # 11.1 Общие принципы моделирования нагрузки
        if data.get("load_modeling_principles"):
            sections.append(("Общие принципы моделирования нагрузки", 2))
            content_parts.append('<h2>11.1 Общие принципы моделирования нагрузки</h2>')
            content_parts.append(render_text_field(data["load_modeling_principles"]))
        
        # 11.2 Профили нагрузки
        if data.get("load_profiles_intro") or data.get("load_profiles_table"):
            sections.append(("Профили нагрузки", 2))
            content_parts.append('<h2>11.2 Профили нагрузки</h2>')
            if data.get("load_profiles_intro"):
                intro_text = data["load_profiles_intro"]
                intro_text = replace_table_references(intro_text, {9: table_num})
                content_parts.append(render_text_field(intro_text))
            if data.get("load_profiles_table"):
                table_html, table_num = render_table_from_text(
                    data["load_profiles_table"],
                    table_num=table_num,
                    caption="Профиль Р1"
                )
                content_parts.append(table_html)
        
        # 11.3 Сценарии использования
        if data.get("use_scenarios_intro") or data.get("use_scenarios_table"):
            sections.append(("Сценарии использования", 2))
            content_parts.append('<h2>11.3 Сценарии использования</h2>')
            if data.get("use_scenarios_intro"):
                intro_text = data["use_scenarios_intro"]
                intro_text = replace_table_references(intro_text, {10: table_num})
                content_parts.append(render_text_field(intro_text))
            if data.get("use_scenarios_table"):
                table_html, table_num = render_table_from_text(
                    data["use_scenarios_table"],
                    table_num=table_num,
                    caption="Описание операции"
                )
                content_parts.append(table_html)
        
        # 11.4 Описание работы эмуляторов
        if data.get("emulators_description"):
            sections.append(("Описание работы эмуляторов", 2))
            content_parts.append('<h2>11.4 Описание работы эмуляторов</h2>')
            content_parts.append(render_text_field(data["emulators_description"]))
    
    # Раздел 12: Мониторинг
    if data.get("monitoring_intro") or data.get("monitoring_tools_table") or data.get("system_resources_table") or data.get("business_metrics_table"):
        sections.append(("Мониторинг", 1))
        content_parts.append('<h1>12 Мониторинг</h1>')
        
        if data.get("monitoring_intro"):
            content_parts.append(render_text_field(data["monitoring_intro"]))
        
        # 12.1 Описание средств мониторинга
        if data.get("monitoring_tools_intro") or data.get("monitoring_tools_table") or data.get("monitoring_tools_note"):
            sections.append(("Описание средств мониторинга", 2))
            content_parts.append('<h2>12.1 Описание средств мониторинга</h2>')
            if data.get("monitoring_tools_intro"):
                intro_text = data["monitoring_tools_intro"]
                intro_text = replace_table_references(intro_text, {11: table_num})
                content_parts.append(render_text_field(intro_text))
            if data.get("monitoring_tools_table"):
                table_html, table_num = render_table_from_text(
                    data["monitoring_tools_table"],
                    table_num=table_num,
                    caption="Средства мониторинга"
                )
                content_parts.append(table_html)
            if data.get("monitoring_tools_note"):
                content_parts.append(render_text_field(data["monitoring_tools_note"]))
        
        # 12.2 Описание метрик мониторинга
        if data.get("system_resources_table") or data.get("business_metrics_table"):
            sections.append(("Описание метрик мониторинга", 2))
            content_parts.append('<h2>12.2 Описание метрик мониторинга</h2>')
            
            # 12.2.1 Мониторинг системных ресурсов
            if data.get("system_resources_intro") or data.get("system_resources_table"):
                sections.append(("Мониторинг системных ресурсов", 3))
                content_parts.append('<h3>12.2.1 Мониторинг системных ресурсов</h3>')
                if data.get("system_resources_intro"):
                    intro_text = data["system_resources_intro"]
                    intro_text = replace_table_references(intro_text, {12: table_num})
                    content_parts.append(render_text_field(intro_text))
                if data.get("system_resources_table"):
                    table_html, table_num = render_table_from_text(
                        data["system_resources_table"],
                        table_num=table_num,
                        caption="Метрики утилизации аппаратных ресурсов и системные метрики"
                    )
                    content_parts.append(table_html)
            
            # 12.2.2 Мониторинг бизнес-метрик
            if data.get("business_metrics_intro") or data.get("business_metrics_table"):
                sections.append(("Мониторинг бизнес-метрик", 3))
                content_parts.append('<h3>12.2.2 Мониторинг бизнес-метрик</h3>')
                if data.get("business_metrics_intro"):
                    intro_text = data["business_metrics_intro"]
                    intro_text = replace_table_references(intro_text, {13: table_num})
                    content_parts.append(render_text_field(intro_text))
                if data.get("business_metrics_table"):
                    table_html, table_num = render_table_from_text(
                        data["business_metrics_table"],
                        table_num=table_num,
                        caption="Бизнес-метрики производительности"
                    )
                    content_parts.append(table_html)
    
    # Раздел 13: Требования к Заказчику
    if data.get("customer_requirements_list"):
        sections.append(("Требования к Заказчику", 1))
        content_parts.append('<h1>13 Требования к Заказчику</h1>')
        content_parts.append(render_list_field(data["customer_requirements_list"], ordered=True))
    
    # Раздел 14: Материалы, подлежащие сдаче
    if data.get("deliverables_intro") or data.get("deliverables_table") or data.get("deliverables_working_docs_table"):
        sections.append(("Материалы, подлежащие сдаче", 1))
        content_parts.append('<h1>14 Материалы, подлежащие сдаче</h1>')
        if data.get("deliverables_intro"):
            intro_text = data["deliverables_intro"]
            intro_text = replace_table_references(intro_text, {14: table_num})
            content_parts.append(render_text_field(intro_text))
        if data.get("deliverables_table"):
            table_html, table_num = render_table_from_text(
                data["deliverables_table"],
                table_num=table_num,
                caption="Материалы, подлежащие сдаче"
            )
            content_parts.append(table_html)
        if data.get("deliverables_working_docs_table"):
            # Обрабатываем вторую таблицу отдельно
            working_docs_data = data["deliverables_working_docs_table"]
            lines = [line.strip() for line in working_docs_data.split('\n') if line.strip()]
            
            if lines:
                # Первая строка - заголовок
                header = lines[0]
                content_parts.append(f'<p><strong>{escape_xml(header)}</strong></p>')
                
                # Остальные строки - таблица
                if len(lines) > 1:
                    table_data = '\n'.join(lines[1:])
                    # Добавляем заголовки столбцов
                    table_data = 'Документ|Подготавливается в результате деятельности\n' + table_data
                    table_html, table_num = render_table_from_text(
                        table_data,
                        table_num=table_num,
                        caption=""
                    )
                    content_parts.append(table_html)
    
    # Раздел 15: Контакты
    if data.get("contacts_table"):
        sections.append(("Контакты", 1))
        content_parts.append('<h1>15 Контакты</h1>')
        table_html, table_num = render_table_from_text(
            data["contacts_table"],
            table_num=table_num,
            caption="Контакты ответственных лиц"
        )
        content_parts.append(table_html)
    
    # Пользовательские блоки
    custom_sections = data.get("custom_sections") or []
    if custom_sections:
        # Определяем начальный номер для пользовательских блоков (16, 17, 18...)
        custom_section_num = 16
        for custom_section in custom_sections:
            title = custom_section.get('title', f'Раздел {custom_section_num}')
            sections.append((title.split('.', 1)[-1].strip() if '.' in title else title, 1))
            
            # Если название уже содержит номер, используем его, иначе добавляем
            if not title[0].isdigit():
                title = f"{custom_section_num}. {title}"
            
            content_parts.append(f'<h1>{escape_xml(title)}</h1>')
            
            # Текст
            if custom_section.get('text'):
                content_parts.append(render_text_field(custom_section['text']))
            
            # Таблица
            if custom_section.get('table'):
                table_html, table_num = render_table_from_text(
                    custom_section['table'],
                    table_num=table_num,
                    caption=None
                )
                content_parts.append(table_html)
            
            # Список
            if custom_section.get('list'):
                content_parts.append(render_list_field(custom_section['list'], ordered=False))
            
            custom_section_num += 1
    
    # Генерация содержания (вставляем в начало после заголовка)
    toc_html = generate_table_of_contents(sections)
    
    # Добавляем другие изображения в конец
    if other_images:
        for img_filename in other_images:
            img_html, figure_num = render_image_macro(img_filename, figure_num=figure_num)
            content_parts.append(img_html)
    
    # Формируем финальный контент: заголовок -> содержание -> остальное
    # content_parts уже содержит заголовок в начале, нам нужно вставить содержание после него
    final_content = []
    
    # Берем заголовок из начала content_parts
    if content_parts:
        final_content.append(content_parts[0])  # Заголовок документа
    
    # Вставляем содержание после заголовка
    if toc_html:
        final_content.append(toc_html)
    
    # Добавляем остальной контент (без повторения заголовка)
    if len(content_parts) > 1:
        final_content.extend(content_parts[1:])
    
    return ''.join(final_content)
