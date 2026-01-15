"""Модуль для экспорта МНТ в различные форматы"""
from typing import Dict, Any
from datetime import datetime
from app.render import render_mnt_to_confluence_storage
import html
import re


def confluence_storage_to_html(storage_xml: str) -> str:
    """Конвертация Confluence Storage Format XML в HTML"""
    # Упрощенная конвертация основных тегов
    html_text = storage_xml
    
    # Заменяем основные теги Confluence на HTML
    html_text = re.sub(r'<ac:structured-macro[^>]*ac:name="info"[^>]*>(.*?)</ac:structured-macro>', r'<div class="info-box">\1</div>', html_text, flags=re.DOTALL)
    html_text = re.sub(r'<ac:parameter[^>]*>(.*?)</ac:parameter>', r'', html_text, flags=re.DOTALL)
    html_text = re.sub(r'<ac:rich-text-body>(.*?)</ac:rich-text-body>', r'\1', html_text, flags=re.DOTALL)
    
    # Убираем namespace префиксы
    html_text = re.sub(r'</?ac:[^>]*>', '', html_text)
    html_text = re.sub(r'</?ri:[^>]*>', '', html_text)
    
    # Заменяем таблицы
    html_text = re.sub(r'<table[^>]*>', '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">', html_text)
    
    return html_text


def parse_table_text(text: str) -> list:
    """Парсинг таблицы из текстового формата (pipe-separated)"""
    if not text:
        return []
    rows = []
    for line in text.strip().split('\n'):
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if cells:
                rows.append(cells)
    return rows


def export_to_html(data: Dict[str, Any]) -> str:
    """Экспорт МНТ в HTML формат с полным содержимым"""
    # Генерируем Confluence Storage Format
    storage_xml = render_mnt_to_confluence_storage(data)
    
    # Конвертируем в HTML
    content_html = confluence_storage_to_html(storage_xml)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(data.get('project_name', 'МНТ'))}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #3b82f6; margin-top: 30px; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; }}
        h3 {{ color: #60a5fa; margin-top: 20px; }}
        h4 {{ color: #93c5fd; margin-top: 15px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        table th, table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        table th {{ background-color: #f2f2f2; font-weight: bold; }}
        ul, ol {{ margin: 10px 0; padding-left: 30px; }}
        p {{ margin: 10px 0; }}
        .info-box {{ background: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px; margin: 10px 0; }}
        .export-meta {{ color: #666; font-size: 0.9em; border-top: 1px solid #ddd; margin-top: 30px; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="export-content">
        {content_html}
    </div>
    <div class="export-meta">
        <p><em>Экспортировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</em></p>
    </div>
</body>
</html>"""
    return html_content


def storage_to_text(storage_xml: str) -> str:
    """Конвертация Confluence Storage Format в простой текст"""
    text = storage_xml
    
    # Убираем XML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Восстанавливаем структуру заголовков и списков
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if line:
            result.append(line)
    
    return '\n'.join(result)


def export_to_text(data: Dict[str, Any]) -> str:
    """Экспорт МНТ в текстовый формат с полным содержимым"""
    # Генерируем Confluence Storage Format
    storage_xml = render_mnt_to_confluence_storage(data)
    
    # Конвертируем в текст
    content_text = storage_to_text(storage_xml)
    
    lines = [
        "=" * 80,
        "МЕТОДИКА НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ",
        "=" * 80,
        "",
        f"Проект: {data.get('project_name', '')}",
        f"Автор: {data.get('author', '')}",
        f"Версия системы: {data.get('system_version', '')}",
        "",
        "-" * 80,
        "",
        content_text,
        "",
        "-" * 80,
        f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "=" * 80,
    ]
    return "\n".join(lines)
