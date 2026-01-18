"""Операции с базой данных"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
import re
from app.core.models import MNTDocument, MNTStatus
from app.utils.logger import logger


def create_mnt(db: Session, data: dict, confluence_space: str, confluence_parent_id: Optional[int] = None) -> dict:
    """Создание нового МНТ в БД"""
    query = text("""
        INSERT INTO mnt.documents (title, project, author, data_json, confluence_space, confluence_parent_id, status)
        VALUES (:title, :project, :author, :data_json, :confluence_space, :confluence_parent_id, :status)
        RETURNING id, created_at, updated_at
    """)
    
    # Убираем служебные поля из data_json, они уже в отдельных колонках
    data_for_json = {k: v for k, v in data.items() if k not in ["title", "project", "author"]}
    
    # Логируем теги перед сохранением
    if "tags" in data_for_json:
        logger.debug(f"CREATE_MNT: Сохраняем теги в data_json: {data_for_json.get('tags')}")
    else:
        logger.warning(f"CREATE_MNT: Теги НЕ найдены в data_for_json! Доступные ключи: {list(data_for_json.keys())}")
    
    result = db.execute(query, {
        "title": data.get("title", ""),
        "project": data.get("project", ""),
        "author": data.get("author", ""),
        "data_json": json.dumps(data_for_json, ensure_ascii=False),
        "confluence_space": confluence_space,
        "confluence_parent_id": confluence_parent_id,
        "status": "draft"
    })
    db.commit()
    
    row = result.fetchone()
    return {
        "id": row[0],
        "created_at": row[1],
        "updated_at": row[2]
    }


def get_mnt(db: Session, mnt_id: int) -> Optional[dict]:
    """Получение МНТ по ID"""
    query = text("""
        SELECT id, title, project, author, created_at, updated_at, status, data_json,
               confluence_space, confluence_parent_id, confluence_page_id, confluence_page_url,
               last_publish_at, last_error
        FROM mnt.documents
        WHERE id = :id
    """)
    
    result = db.execute(query, {"id": mnt_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    # data_json может быть уже dict (JSONB) или строкой, в зависимости от драйвера БД
    data_json_value = row[7]
    if data_json_value:
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        else:
            data_json_dict = json.loads(data_json_value)
    else:
        data_json_dict = {}
    
    return {
        "id": row[0],
        "title": row[1],
        "project": row[2],
        "author": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "status": row[6],
        "data_json": data_json_dict,
        "confluence_space": row[8],
        "confluence_parent_id": row[9],
        "confluence_page_id": row[10],
        "confluence_page_url": row[11],
        "last_publish_at": row[12],
        "last_error": row[13]
    }


def update_mnt(db: Session, mnt_id: int, data: dict, confluence_space: str, confluence_parent_id: Optional[int] = None, status: Optional[str] = None) -> bool:
    """Обновление МНТ
    
    Args:
        status: Если указан, устанавливает статус. Если None - статус не меняется.
                Обычно используется для установки 'draft' при сохранении без публикации.
    """
    # Убираем служебные поля из data_json, они уже в отдельных колонках
    data_for_json = {k: v for k, v in data.items() if k not in ["title", "project", "author"]}
    
    # Логируем теги перед сохранением
    if "tags" in data_for_json:
        logger.debug(f"UPDATE_MNT: Сохраняем теги в data_json: {data_for_json.get('tags')}")
    else:
        logger.warning(f"UPDATE_MNT: Теги НЕ найдены в data_for_json! Доступные ключи: {list(data_for_json.keys())}")
    
    if status:
        query = text("""
            UPDATE mnt.documents
            SET title = :title,
                project = :project,
                author = :author,
                data_json = :data_json,
                confluence_space = :confluence_space,
                confluence_parent_id = :confluence_parent_id,
                status = :status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """)
        params = {
            "id": mnt_id,
            "title": data.get("title", ""),
            "project": data.get("project", ""),
            "author": data.get("author", ""),
            "data_json": json.dumps(data_for_json, ensure_ascii=False),
            "confluence_space": confluence_space,
            "confluence_parent_id": confluence_parent_id,
            "status": status
        }
    else:
        query = text("""
            UPDATE mnt.documents
            SET title = :title,
                project = :project,
                author = :author,
                data_json = :data_json,
                confluence_space = :confluence_space,
                confluence_parent_id = :confluence_parent_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """)
        params = {
            "id": mnt_id,
            "title": data.get("title", ""),
            "project": data.get("project", ""),
            "author": data.get("author", ""),
            "data_json": json.dumps(data_for_json, ensure_ascii=False),
            "confluence_space": confluence_space,
            "confluence_parent_id": confluence_parent_id
        }
    
    result = db.execute(query, params)
    db.commit()
    
    return result.rowcount > 0


def list_mnt(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    tag_id: Optional[str] = None,  # Изменено на str для поиска по тексту
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    include_deleted: bool = False  # Если True - показывать только удаленные, если False - только не удаленные
) -> tuple[List[dict], int]:
    """Список МНТ с пагинацией, поиском, фильтрами и сортировкой"""
    # Формируем условия поиска и фильтров
    conditions = []
    search_params = {}
    
    # Фильтр по deleted_at
    if include_deleted:
        # Показываем только удаленные (в корзине)
        conditions.append("d.deleted_at IS NOT NULL")
    else:
        # Показываем только не удаленные (обычный список)
        conditions.append("d.deleted_at IS NULL")
    
    if search and search.strip():
        # Расширенный поиск: по полям и по содержимому JSON
        search_term = f"%{search.strip()}%"
        conditions.append("""
            (title ILIKE :search 
             OR project ILIKE :search 
             OR author ILIKE :search
             OR data_json::text ILIKE :search)
        """)
        search_params["search"] = search_term
    
    if status and status.strip():
        conditions.append("status = :status")
        search_params["status"] = status.strip()
    
    if author and author.strip():
        conditions.append("author ILIKE :author")
        search_params["author"] = f"%{author.strip()}%"
    
    # Фильтр по тегам - ищем в JSONB массиве tags
    tag_join = ""
    if tag_id and isinstance(tag_id, str) and tag_id.strip():
        # Ищем тег в JSONB массиве tags
        tag_search_term = tag_id.strip()
        conditions.append("EXISTS (SELECT 1 FROM jsonb_array_elements_text(data_json->'tags') AS tag WHERE tag ILIKE :tag_search)")
        search_params["tag_search"] = f"%{tag_search_term}%"
    
    # Используем алиас d для documents
    from_clause = f"FROM mnt.documents d {tag_join}" if tag_join else "FROM mnt.documents d"
    
    # Исправляем условия - заменяем поля на d.field если есть JOIN
    if conditions:
        fixed_conditions = []
        for condition in conditions:
            # Если есть JOIN, заменяем прямые обращения к полям на d.field (кроме JOIN условий)
            if tag_join and "dt.tag_id" not in condition and "d." not in condition:
                # Заменяем поля таблицы на d.field
                condition = re.sub(r'\btitle\b', 'd.title', condition)
                condition = re.sub(r'\bproject\b', 'd.project', condition)
                condition = re.sub(r'\bauthor\b', 'd.author', condition)
                condition = re.sub(r'\bstatus\b', 'd.status', condition)
            elif not tag_join and "d." not in condition:
                # Даже без JOIN используем d. для единообразия
                condition = re.sub(r'\btitle\b', 'd.title', condition)
                condition = re.sub(r'\bproject\b', 'd.project', condition)
                condition = re.sub(r'\bauthor\b', 'd.author', condition)
                condition = re.sub(r'\bstatus\b', 'd.status', condition)
            fixed_conditions.append(condition)
        search_condition = "WHERE " + " AND ".join(fixed_conditions)
    else:
        search_condition = ""
    
    # Получаем общее количество
    count_query = text(f"SELECT COUNT(DISTINCT d.id) {from_clause} {search_condition}")
    total_result = db.execute(count_query, search_params)
    total = total_result.scalar()
    
    # Валидация и формирование сортировки
    valid_sort_columns = {
        "id": "d.id",
        "title": "d.title",
        "project": "d.project",
        "author": "d.author",
        "created_at": "d.created_at",
        "updated_at": "d.updated_at",
        "status": "d.status"
    }
    sort_column = valid_sort_columns.get(sort_by, "d.created_at")
    sort_dir = "DESC" if sort_order.lower() == "desc" else "ASC"
    
    # Получаем список
    query = text(f"""
        SELECT DISTINCT d.id, d.title, d.project, d.author, d.created_at, d.updated_at, d.status, 
               d.confluence_space, d.confluence_page_id, d.confluence_page_url, d.data_json,
               d.last_publish_at, d.last_error, d.deleted_at
        {from_clause}
        {search_condition}
        ORDER BY {sort_column} {sort_dir}
        LIMIT :limit OFFSET :skip
    """)
    
    query_params = {"limit": limit, "skip": skip, **search_params}
    result = db.execute(query, query_params)
    rows = result.fetchall()
    
    documents = []
    for row in rows:
        # Обрабатываем data_json
        data_json_value = row[10] if len(row) > 10 else None
        data_json_dict = {}
        if data_json_value:
            if isinstance(data_json_value, dict):
                data_json_dict = data_json_value
            elif isinstance(data_json_value, str):
                try:
                    data_json_dict = json.loads(data_json_value)
                except:
                    data_json_dict = {}
        
        documents.append({
            "id": row[0],
            "title": row[1],
            "project": row[2],
            "author": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "status": row[6],
            "confluence_space": row[7],
            "confluence_page_id": row[8],
            "confluence_page_url": row[9],
            "data_json": data_json_dict,
            "last_publish_at": row[11] if len(row) > 11 else None,
            "last_error": row[12] if len(row) > 12 else None,
            "deleted_at": row[13] if len(row) > 13 else None
        })
    
    return documents, total


def update_confluence_info(db: Session, mnt_id: int, page_id: int, page_url: str, status: str = "published", error: Optional[str] = None) -> bool:
    """Обновление информации о Confluence странице"""
    query = text("""
        UPDATE mnt.documents
        SET confluence_page_id = :page_id,
            confluence_page_url = :page_url,
            status = :status,
            last_publish_at = CURRENT_TIMESTAMP,
            last_error = :error
        WHERE id = :id
    """)
    
    result = db.execute(query, {
        "id": mnt_id,
        "page_id": page_id,
        "page_url": page_url,
        "status": status,
        "error": error
    })
    db.commit()
    
    return result.rowcount > 0


def set_error_status(db: Session, mnt_id: int, error_message: str) -> bool:
    """Установка статуса ошибки"""
    query = text("""
        UPDATE mnt.documents
        SET status = 'error',
            last_error = :error
        WHERE id = :id
    """)
    
    result = db.execute(query, {"id": mnt_id, "error": error_message})
    db.commit()
    
    return result.rowcount > 0


# ==================== История действий ====================

def log_action(
    db: Session,
    mnt_id: int,
    user_name: str,
    action_type: str,
    action_description: str = "",
    details: Optional[dict] = None
) -> bool:
    """Логирование действия пользователя с МНТ"""
    try:
        query = text("""
            INSERT INTO mnt.action_history (mnt_id, user_name, action_type, action_description, details)
            VALUES (:mnt_id, :user_name, :action_type, :action_description, :details)
        """)
        
        db.execute(query, {
            "mnt_id": mnt_id,
            "user_name": user_name,
            "action_type": action_type,
            "action_description": action_description,
            "details": json.dumps(details, ensure_ascii=False) if details else None
        })
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def get_action_history(db: Session, mnt_id: int, limit: int = 100) -> List[dict]:
    """Получение истории действий для МНТ"""
    query = text("""
        SELECT id, user_name, action_type, action_description, details, created_at
        FROM mnt.action_history
        WHERE mnt_id = :mnt_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"mnt_id": mnt_id, "limit": limit})
    rows = result.fetchall()
    
    history = []
    for row in rows:
        details_value = row[4]
        if details_value:
            if isinstance(details_value, dict):
                details_dict = details_value
            else:
                details_dict = json.loads(details_value) if details_value else {}
        else:
            details_dict = {}
        
        history.append({
            "id": row[0],
            "user_name": row[1],
            "action_type": row[2],
            "action_description": row[3],
            "details": details_dict,
            "created_at": row[5]
        })
    
    return history
def get_tags(db: Session) -> List[dict]:
    """Получение всех тегов"""
    query = text("""
        SELECT id, name, color
        FROM mnt.tags
        ORDER BY name
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    return [{"id": row[0], "name": row[1], "color": row[2]} for row in rows]


def create_tag(db: Session, name: str, color: str = "#6c757d") -> dict:
    """Создание нового тега"""
    query = text("""
        INSERT INTO mnt.tags (name, color)
        VALUES (:name, :color)
        RETURNING id, name, color
    """)
    
    result = db.execute(query, {"name": name, "color": color})
    db.commit()
    
    row = result.fetchone()
    return {"id": row[0], "name": row[1], "color": row[2]}


def get_document_tags(db: Session, document_id: int) -> List[dict]:
    """Получение тегов документа"""
    query = text("""
        SELECT t.id, t.name, t.color
        FROM mnt.tags t
        INNER JOIN mnt.document_tags dt ON t.id = dt.tag_id
        WHERE dt.document_id = :document_id
    """)
    
    result = db.execute(query, {"document_id": document_id})
    rows = result.fetchall()
    
    return [{"id": row[0], "name": row[1], "color": row[2]} for row in rows]


def set_document_tags(db: Session, document_id: int, tag_ids: List[int]) -> bool:
    """Установка тегов для документа"""
    try:
        # Удаляем старые теги
        delete_query = text("DELETE FROM mnt.document_tags WHERE document_id = :document_id")
        db.execute(delete_query, {"document_id": document_id})
        
        # Добавляем новые теги
        if tag_ids:
            insert_query = text("""
                INSERT INTO mnt.document_tags (document_id, tag_id)
                VALUES (:document_id, :tag_id)
            """)
            for tag_id in tag_ids:
                db.execute(insert_query, {"document_id": document_id, "tag_id": tag_id})
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def soft_delete_mnt(db: Session, mnt_id: int) -> bool:
    """Мягкое удаление МНТ (soft delete) - устанавливает deleted_at"""
    query = text("""
        UPDATE mnt.documents
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = :id AND deleted_at IS NULL
    """)
    
    result = db.execute(query, {"id": mnt_id})
    db.commit()
    
    return result.rowcount > 0


def restore_mnt(db: Session, mnt_id: int) -> bool:
    """Восстановление удаленного МНТ - очищает deleted_at"""
    query = text("""
        UPDATE mnt.documents
        SET deleted_at = NULL
        WHERE id = :id AND deleted_at IS NOT NULL
    """)
    
    result = db.execute(query, {"id": mnt_id})
    db.commit()
    
    return result.rowcount > 0


def permanently_delete_old_mnts(db: Session, days: int = 30) -> int:
    """Окончательное удаление МНТ, которые были удалены более N дней назад
    
    Args:
        days: Количество дней, после которых удаление становится окончательным
    
    Returns:
        Количество окончательно удаленных записей
    """
    query = text("""
        DELETE FROM mnt.documents
        WHERE deleted_at IS NOT NULL
          AND deleted_at < CURRENT_TIMESTAMP - INTERVAL ':days days'
    """)
    
    result = db.execute(query, {"days": days})
    db.commit()
    
    return result.rowcount


def get_mnt_with_deleted(db: Session, mnt_id: int, include_deleted: bool = True) -> Optional[dict]:
    """Получение МНТ по ID, включая удаленные (если include_deleted=True)"""
    if include_deleted:
        # Можем получить даже удаленный
        query = text("""
            SELECT id, title, project, author, created_at, updated_at, status, data_json,
                   confluence_space, confluence_parent_id, confluence_page_id, confluence_page_url,
                   last_publish_at, last_error, deleted_at
            FROM mnt.documents
            WHERE id = :id
        """)
    else:
        # Только не удаленные
        query = text("""
            SELECT id, title, project, author, created_at, updated_at, status, data_json,
                   confluence_space, confluence_parent_id, confluence_page_id, confluence_page_url,
                   last_publish_at, last_error, deleted_at
            FROM mnt.documents
            WHERE id = :id AND deleted_at IS NULL
        """)
    
    result = db.execute(query, {"id": mnt_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    # Обрабатываем data_json
    data_json_value = row[7]
    if isinstance(data_json_value, dict):
        data_json_dict = data_json_value
    elif isinstance(data_json_value, str):
        try:
            data_json_dict = json.loads(data_json_value)
        except:
            data_json_dict = {}
    else:
        data_json_dict = {}
    
    return {
        "id": row[0],
        "title": row[1],
        "project": row[2],
        "author": row[3],
        "created_at": row[4],
        "updated_at": row[5],
        "status": row[6],
        "data_json": data_json_dict,
        "confluence_space": row[8],
        "confluence_parent_id": row[9],
        "confluence_page_id": row[10],
        "confluence_page_url": row[11],
        "last_publish_at": row[12],
        "last_error": row[13],
        "deleted_at": row[14] if len(row) > 14 else None
    }


# ========== Функции для работы с версиями МНТ ==========

def increment_version_number(version_str: str) -> str:
    """Инкрементирует номер версии
    
    Примеры:
        "0.1" -> "0.2"
        "0.9" -> "1.0"
        "1.5" -> "1.6"
        "2.0" -> "2.1"
    """
    if not version_str:
        return "0.1"
    
    # Парсим версию формата "X.Y"
    parts = version_str.split(".")
    if len(parts) != 2:
        # Если формат неверный, возвращаем "0.1"
        logger.warning(f"Неверный формат версии: {version_str}, используем 0.1")
        return "0.1"
    
    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError:
        logger.warning(f"Неверный формат версии: {version_str}, используем 0.1")
        return "0.1"
    
    # Инкрементируем минорную часть
    minor += 1
    
    # Если минорная часть стала 10, увеличиваем мажорную и сбрасываем минорную
    if minor >= 10:
        major += 1
        minor = 0
    
    return f"{major}.{minor}"


def get_latest_version_from_history(data_json: dict) -> str:
    """Извлекает последнюю версию из таблицы 'История изменений' (раздел 1)
    
    Возвращает максимальную версию по числовому значению.
    Если версий нет, возвращает None.
    """
    history_table = data_json.get("history_changes_table", "")
    if not history_table:
        return None
    
    # Парсим таблицу: каждая строка - запись, разделитель | между колонками
    lines = [line.strip() for line in history_table.split('\n') if line.strip()]
    if not lines:
        return None
    
    # Пропускаем заголовок (первая строка), если есть
    # Ищем версии в формате "X.Y"
    versions = []
    version_pattern = re.compile(r'^(\d+)\.(\d+)$')
    
    for line in lines[1:]:  # Пропускаем заголовок
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 2:  # Дата|Версия|Описание|Автор
            version_str = parts[1].strip()
            if version_pattern.match(version_str):
                versions.append(version_str)
    
    if not versions:
        return None
    
    # Сортируем версии по числовому значению
    def version_key(v):
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]))
    
    latest_version = max(versions, key=version_key)
    return latest_version


def create_document_version(
    db: Session,
    mnt_id: int,
    version_number: str,
    title: str,
    project: str,
    author: str,
    data_json: dict,
    status: str,
    confluence_space: Optional[str] = None,
    confluence_parent_id: Optional[int] = None,
    confluence_page_id: Optional[int] = None,
    confluence_page_url: Optional[str] = None,
    last_publish_at: Optional[datetime] = None,
    created_by: str = None
) -> dict:
    """Создание новой версии МНТ документа"""
    query = text("""
        INSERT INTO mnt.document_versions (
            mnt_id, version_number, title, project, author, data_json, status,
            confluence_space, confluence_parent_id, confluence_page_id, 
            confluence_page_url, last_publish_at, created_by
        )
        VALUES (
            :mnt_id, :version_number, :title, :project, :author, :data_json, :status,
            :confluence_space, :confluence_parent_id, :confluence_page_id,
            :confluence_page_url, :last_publish_at, :created_by
        )
        RETURNING id, created_at
    """)
    
    result = db.execute(query, {
        "mnt_id": mnt_id,
        "version_number": version_number,
        "title": title,
        "project": project,
        "author": author,
        "data_json": json.dumps(data_json, ensure_ascii=False),
        "status": status,
        "confluence_space": confluence_space,
        "confluence_parent_id": confluence_parent_id,
        "confluence_page_id": confluence_page_id,
        "confluence_page_url": confluence_page_url,
        "last_publish_at": last_publish_at,
        "created_by": created_by or author
    })
    db.commit()
    
    row = result.fetchone()
    return {
        "id": row[0],
        "created_at": row[1]
    }


def get_document_versions(
    db: Session,
    mnt_id: int,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[dict], int]:
    """Получение списка версий МНТ документа с пагинацией
    
    Returns:
        Tuple[List[dict], int]: (список версий, общее количество)
    """
    # Получаем общее количество
    count_query = text("""
        SELECT COUNT(*) FROM mnt.document_versions
        WHERE mnt_id = :mnt_id
    """)
    count_result = db.execute(count_query, {"mnt_id": mnt_id})
    total = count_result.scalar()
    
    # Получаем версии с пагинацией
    query = text("""
        SELECT id, mnt_id, version_number, title, project, author, data_json,
               status, confluence_space, confluence_parent_id, confluence_page_id,
               confluence_page_url, last_publish_at, created_at, created_by
        FROM mnt.document_versions
        WHERE mnt_id = :mnt_id
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {
        "mnt_id": mnt_id,
        "limit": limit,
        "skip": skip
    })
    
    versions = []
    for row in result.fetchall():
        # Обрабатываем data_json
        data_json_value = row[6]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        elif isinstance(data_json_value, str):
            try:
                data_json_dict = json.loads(data_json_value)
            except:
                data_json_dict = {}
        else:
            data_json_dict = {}
        
        versions.append({
            "id": row[0],
            "mnt_id": row[1],
            "version_number": row[2],
            "title": row[3],
            "project": row[4],
            "author": row[5],
            "data_json": data_json_dict,
            "status": row[7],
            "confluence_space": row[8],
            "confluence_parent_id": row[9],
            "confluence_page_id": row[10],
            "confluence_page_url": row[11],
            "last_publish_at": row[12],
            "created_at": row[13],
            "created_by": row[14]
        })
    
    return versions, total


def get_document_version(db: Session, version_id: int) -> Optional[dict]:
    """Получение конкретной версии МНТ по ID версии"""
    query = text("""
        SELECT id, mnt_id, version_number, title, project, author, data_json,
               status, confluence_space, confluence_parent_id, confluence_page_id,
               confluence_page_url, last_publish_at, created_at, created_by
        FROM mnt.document_versions
        WHERE id = :version_id
    """)
    
    result = db.execute(query, {"version_id": version_id})
    row = result.fetchone()
    
    if not row:
        return None
    
    # Обрабатываем data_json
    data_json_value = row[6]
    if isinstance(data_json_value, dict):
        data_json_dict = data_json_value
    elif isinstance(data_json_value, str):
        try:
            data_json_dict = json.loads(data_json_value)
        except:
            data_json_dict = {}
    else:
        data_json_dict = {}
    
    return {
        "id": row[0],
        "mnt_id": row[1],
        "version_number": row[2],
        "title": row[3],
        "project": row[4],
        "author": row[5],
        "data_json": data_json_dict,
        "status": row[7],
        "confluence_space": row[8],
        "confluence_parent_id": row[9],
        "confluence_page_id": row[10],
        "confluence_page_url": row[11],
        "last_publish_at": row[12],
        "created_at": row[13],
        "created_by": row[14]
    }


def get_unfinished_drafts(db: Session, days: int = 7) -> List[dict]:
    """
    Получить список незавершенных МНТ (черновики старше N дней)
    
    Args:
        db: Сессия БД
        days: Количество дней (по умолчанию 7)
    
    Returns:
        Список МНТ документов
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    query = text("""
        SELECT id, title, project, author, created_at, updated_at, status, data_json,
               confluence_space, confluence_parent_id, confluence_page_id, confluence_page_url,
               last_publish_at, last_error
        FROM mnt.documents
        WHERE status = 'draft'
          AND deleted_at IS NULL
          AND updated_at < :cutoff_date
        ORDER BY updated_at ASC
    """)
    
    result = db.execute(query, {"cutoff_date": cutoff_date})
    rows = result.fetchall()
    
    documents = []
    for row in rows:
        data_json_value = row[7]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        elif isinstance(data_json_value, str):
            try:
                data_json_dict = json.loads(data_json_value)
            except:
                data_json_dict = {}
        else:
            data_json_dict = {}
        
        documents.append({
            "id": row[0],
            "title": row[1],
            "project": row[2],
            "author": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "status": row[6],
            "data_json": data_json_dict,
            "confluence_space": row[8],
            "confluence_parent_id": row[9],
            "confluence_page_id": row[10],
            "confluence_page_url": row[11],
            "last_publish_at": row[12],
            "last_error": row[13]
        })
    
    return documents


def get_documents_needing_update(db: Session, days: int = 30) -> List[dict]:
    """
    Получить список МНТ, требующих обновления (опубликованные, но не обновлялись более N дней)
    
    Args:
        db: Сессия БД
        days: Количество дней (по умолчанию 30)
    
    Returns:
        Список МНТ документов
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    query = text("""
        SELECT id, title, project, author, created_at, updated_at, status, data_json,
               confluence_space, confluence_parent_id, confluence_page_id, confluence_page_url,
               last_publish_at, last_error
        FROM mnt.documents
        WHERE status = 'published'
          AND deleted_at IS NULL
          AND confluence_page_id IS NOT NULL
          AND (
              last_publish_at IS NULL 
              OR last_publish_at < :cutoff_date
              OR updated_at > last_publish_at
          )
        ORDER BY updated_at DESC
    """)
    
    result = db.execute(query, {"cutoff_date": cutoff_date})
    rows = result.fetchall()
    
    documents = []
    for row in rows:
        data_json_value = row[7]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        elif isinstance(data_json_value, str):
            try:
                data_json_dict = json.loads(data_json_value)
            except:
                data_json_dict = {}
        else:
            data_json_dict = {}
        
        documents.append({
            "id": row[0],
            "title": row[1],
            "project": row[2],
            "author": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "status": row[6],
            "data_json": data_json_dict,
            "confluence_space": row[8],
            "confluence_parent_id": row[9],
            "confluence_page_id": row[10],
            "confluence_page_url": row[11],
            "last_publish_at": row[12],
            "last_error": row[13]
        })
    
    return documents


def log_field_change(
    db: Session,
    mnt_id: int,
    field_name: str,
    field_path: str,
    old_value: Any,
    new_value: Any,
    changed_by: str,
    change_type: str = "update",
    description: Optional[str] = None,
    document_version_id: Optional[int] = None
) -> int:
    """
    Записать изменение поля в историю
    
    Args:
        db: Сессия БД
        mnt_id: ID МНТ
        field_name: Название поля
        field_path: Путь к полю (например: "title", "data_json.introduction_text")
        old_value: Старое значение
        new_value: Новое значение
        changed_by: Автор изменения
        change_type: Тип изменения (create, update, delete)
        description: Описание изменения
        document_version_id: ID версии документа (опционально)
    
    Returns:
        ID созданной записи
    """
    # Преобразуем значения в строки для хранения
    if isinstance(old_value, (dict, list)):
        old_value_str = json.dumps(old_value, ensure_ascii=False)
    else:
        old_value_str = str(old_value) if old_value is not None else None
    
    if isinstance(new_value, (dict, list)):
        new_value_str = json.dumps(new_value, ensure_ascii=False)
    else:
        new_value_str = str(new_value) if new_value is not None else None
    
    query = text("""
        INSERT INTO mnt.field_history 
        (mnt_id, field_name, field_path, old_value, new_value, changed_by, change_type, description, document_version_id)
        VALUES (:mnt_id, :field_name, :field_path, :old_value, :new_value, :changed_by, :change_type, :description, :document_version_id)
        RETURNING id
    """)
    
    result = db.execute(query, {
        "mnt_id": mnt_id,
        "field_name": field_name,
        "field_path": field_path,
        "old_value": old_value_str,
        "new_value": new_value_str,
        "changed_by": changed_by,
        "change_type": change_type,
        "description": description,
        "document_version_id": document_version_id
    })
    db.commit()
    
    row = result.fetchone()
    return row[0] if row else None


def get_field_history(
    db: Session,
    mnt_id: int,
    field_name: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """
    Получить историю изменений полей МНТ
    
    Args:
        db: Сессия БД
        mnt_id: ID МНТ
        field_name: Название поля (опционально, если None - все поля)
        limit: Максимум записей
    
    Returns:
        Список записей истории
    """
    if field_name:
        query = text("""
            SELECT id, mnt_id, field_name, field_path, old_value, new_value,
                   changed_by, changed_at, change_type, description, document_version_id
            FROM mnt.field_history
            WHERE mnt_id = :mnt_id AND field_name = :field_name
            ORDER BY changed_at DESC
            LIMIT :limit
        """)
        params = {"mnt_id": mnt_id, "field_name": field_name, "limit": limit}
    else:
        query = text("""
            SELECT id, mnt_id, field_name, field_path, old_value, new_value,
                   changed_by, changed_at, change_type, description, document_version_id
            FROM mnt.field_history
            WHERE mnt_id = :mnt_id
            ORDER BY changed_at DESC
            LIMIT :limit
        """)
        params = {"mnt_id": mnt_id, "limit": limit}
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    history = []
    for row in rows:
        # Пытаемся распарсить JSON значения
        old_value = row[4]
        if old_value:
            try:
                old_value = json.loads(old_value)
            except:
                pass
        
        new_value = row[5]
        if new_value:
            try:
                new_value = json.loads(new_value)
            except:
                pass
        
        history.append({
            "id": row[0],
            "mnt_id": row[1],
            "field_name": row[2],
            "field_path": row[3],
            "old_value": old_value,
            "new_value": new_value,
            "changed_by": row[6],
            "changed_at": row[7],
            "change_type": row[8],
            "description": row[9],
            "document_version_id": row[10]
        })
    
    return history


def get_field_names_for_mnt(db: Session, mnt_id: int) -> List[str]:
    """
    Получить список всех полей, которые были изменены для МНТ
    
    Args:
        db: Сессия БД
        mnt_id: ID МНТ
    
    Returns:
        Список уникальных названий полей
    """
    query = text("""
        SELECT DISTINCT field_name
        FROM mnt.field_history
        WHERE mnt_id = :mnt_id
        ORDER BY field_name
    """)
    
    result = db.execute(query, {"mnt_id": mnt_id})
    return [row[0] for row in result.fetchall()]
