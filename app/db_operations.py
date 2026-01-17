"""Операции с базой данных"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
import json
import re
from app.models import MNTDocument, MNTStatus
from app.logger import logger


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


def save_version(db: Session, document_id: int, data: dict, changed_by: str = "unknown", change_reason: str = "") -> bool:
    """Сохранение версии документа в историю изменений"""
    try:
        # Получаем последнюю версию
        max_version_query = text("""
            SELECT COALESCE(MAX(version_number), 0) 
            FROM mnt.document_versions 
            WHERE document_id = :document_id
        """)
        result = db.execute(max_version_query, {"document_id": document_id})
        max_version = result.scalar() or 0
        new_version = max_version + 1
        
        # Сохраняем версию
        insert_query = text("""
            INSERT INTO mnt.document_versions (document_id, version_number, data_json, changed_by, change_reason)
            VALUES (:document_id, :version_number, :data_json, :changed_by, :change_reason)
        """)
        
        db.execute(insert_query, {
            "document_id": document_id,
            "version_number": new_version,
            "data_json": json.dumps(data, ensure_ascii=False),
            "changed_by": changed_by,
            "change_reason": change_reason
        })
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


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


def get_versions(db: Session, document_id: int) -> List[dict]:
    """Получение истории версий документа"""
    query = text("""
        SELECT id, version_number, data_json, changed_by, change_reason, created_at
        FROM mnt.document_versions
        WHERE document_id = :document_id
        ORDER BY version_number DESC
    """)
    
    result = db.execute(query, {"document_id": document_id})
    rows = result.fetchall()
    
    versions = []
    for row in rows:
        data_json_value = row[2]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        else:
            data_json_dict = json.loads(data_json_value) if data_json_value else {}
        
        versions.append({
            "id": row[0],
            "version_number": row[1],
            "data_json": data_json_dict,
            "changed_by": row[3],
            "change_reason": row[4],
            "created_at": row[5]
        })
    
    return versions


def get_published_version_data(db: Session, document_id: int, last_publish_at) -> Optional[dict]:
    """Получение данных версии, которая была опубликована в Confluence"""
    if not last_publish_at:
        return None
    
    from datetime import timedelta
    from app.logger import logger
    
    # Стратегия 1: Ищем версию с пометкой "после публикации", созданную в интервале [last_publish_at - 1 мин, last_publish_at + 10 мин]
    # Это версия, которая была сохранена сразу после успешной публикации
    start_time = last_publish_at - timedelta(minutes=1)
    end_time = last_publish_at + timedelta(minutes=10)
    
    query = text("""
        SELECT id, version_number, data_json, changed_by, change_reason, created_at
        FROM mnt.document_versions
        WHERE document_id = :document_id
          AND created_at BETWEEN :start_time AND :end_time
          AND (change_reason LIKE '%публикации%' OR change_reason LIKE '%публикация%' OR change_reason LIKE '%publish%')
        ORDER BY ABS(EXTRACT(EPOCH FROM (created_at - :last_publish_at))) ASC, created_at DESC
        LIMIT 1
    """)
    
    result = db.execute(query, {
        "document_id": document_id,
        "start_time": start_time,
        "end_time": end_time,
        "last_publish_at": last_publish_at
    })
    row = result.fetchone()
    
    if row:
        data_json_value = row[2]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        else:
            data_json_dict = json.loads(data_json_value) if data_json_value else {}
        logger.debug(f"МНТ {document_id}: Найдена версия после публикации (стратегия 1): версия {row[1]}, created_at={row[5]}, reason={row[4]}")
        return data_json_dict
    
    # Стратегия 2: Если не нашли по пометке, ищем последнюю версию, созданную в интервале [last_publish_at - 5 мин, last_publish_at + 10 мин]
    # Это может быть версия, которая была сохранена до или сразу после публикации
    start_time_fallback = last_publish_at - timedelta(minutes=5)
    end_time_fallback = last_publish_at + timedelta(minutes=10)
    
    query_fallback = text("""
        SELECT id, version_number, data_json, changed_by, change_reason, created_at
        FROM mnt.document_versions
        WHERE document_id = :document_id
          AND created_at BETWEEN :start_time AND :end_time
        ORDER BY ABS(EXTRACT(EPOCH FROM (created_at - :last_publish_at))) ASC, created_at DESC
        LIMIT 1
    """)
    
    result_fallback = db.execute(query_fallback, {
        "document_id": document_id,
        "start_time": start_time_fallback,
        "end_time": end_time_fallback,
        "last_publish_at": last_publish_at
    })
    row_fallback = result_fallback.fetchone()
    
    if row_fallback:
        data_json_value = row_fallback[2]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        else:
            data_json_dict = json.loads(data_json_value) if data_json_value else {}
        logger.debug(f"МНТ {document_id}: Найдена версия около времени публикации (стратегия 2): версия {row_fallback[1]}, created_at={row_fallback[5]}, reason={row_fallback[4]}")
        return data_json_dict
    
    # Стратегия 3: Если все еще не нашли, ищем последнюю версию, созданную ДО публикации (для старых МНТ)
    query_old = text("""
        SELECT id, version_number, data_json, changed_by, change_reason, created_at
        FROM mnt.document_versions
        WHERE document_id = :document_id
          AND created_at <= :publish_time
        ORDER BY created_at DESC, version_number DESC
        LIMIT 1
    """)
    
    publish_time_with_margin = last_publish_at + timedelta(minutes=5)
    result_old = db.execute(query_old, {
        "document_id": document_id,
        "publish_time": publish_time_with_margin
    })
    row_old = result_old.fetchone()
    
    if row_old:
        data_json_value = row_old[2]
        if isinstance(data_json_value, dict):
            data_json_dict = data_json_value
        else:
            data_json_dict = json.loads(data_json_value) if data_json_value else {}
        logger.debug(f"МНТ {document_id}: Найдена версия до публикации (стратегия 3): версия {row_old[1]}, created_at={row_old[5]}, reason={row_old[4]}")
        return data_json_dict
    
    logger.warning(f"МНТ {document_id}: Не найдена версия на момент публикации (last_publish_at={last_publish_at})")
    return None


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
