"""Главный файл приложения FastAPI"""
from fastapi import FastAPI, Depends, HTTPException, Request, Form, File, UploadFile, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import json
import mimetypes
import io
import csv
import time
import os
from pathlib import Path
import uuid

from app.database import get_db, check_connection
from app.models import MNTData, MNTDocument, MNTCreateRequest, MNTListResponse, MNTUpdateRequest
from app.db_operations import (
    create_mnt, get_mnt, update_mnt, list_mnt,
    update_confluence_info, set_error_status,
    get_tags, create_tag, get_document_tags, set_document_tags,
    log_action, get_action_history,
    soft_delete_mnt, restore_mnt, get_mnt_with_deleted,
    create_document_version, get_latest_version_from_history, increment_version_number,
    get_document_versions, get_document_version,
    get_unfinished_drafts, get_documents_needing_update,
    log_field_change, get_field_history, get_field_names_for_mnt
)
from app.version_diff import compare_versions
from app.diff_tracker import compare_mnt_data
from app.confluence import get_confluence_client, ConfluenceClient, is_confluence_configured
from app.render import render_mnt_to_confluence_storage
from app.defaults import get_default_mnt_data
from app.logger import (
    log_mnt_operation, log_error, log_confluence_operation, 
    log_user_action, log_request, logger, generate_request_id
)
from app.export import export_to_html, export_to_text
from app.completeness_checker import check_document_completeness
from app.tag_templates import get_template_data_for_tags, get_available_templates, apply_template_to_data
from datetime import datetime
from fastapi.responses import Response
import logging

app = FastAPI(title="МНТ Confluence Generator", version="1.0.0")

# Настройка логирования для этого модуля
logger = logging.getLogger("mnt_generator.main")

# Подключение шаблонов
templates = Jinja2Templates(directory="app/templates")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Middleware для логирования всех запросов
class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех HTTP запросов"""
    async def dispatch(self, request: StarletteRequest, call_next):
        # Пропускаем статические файлы
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # Генерируем request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Получаем IP пользователя
        user_ip = request.client.host if request.client else "unknown"
        request.state.user_ip = user_ip
        
        # Начало запроса
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        logger.debug(
            f"ВХОДЯЩИЙ ЗАПРОС | {method} {path}",
            extra={
                'request_id': request_id,
                'user_ip': user_ip,
                'user_name': '-'
            }
        )
        if query_params:
            logger.debug(
                f"Query params: {query_params}",
                extra={
                    'request_id': request_id,
                    'user_ip': user_ip,
                    'user_name': '-'
                }
            )
        
        # Пытаемся получить размер запроса из заголовков
        request_size_bytes = None
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                request_size_bytes = int(content_length)
            except (ValueError, TypeError):
                pass
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Пытаемся определить размер ответа из заголовков
            response_size_bytes = None
            content_length = response.headers.get('content-length')
            if content_length:
                try:
                    response_size_bytes = int(content_length)
                except (ValueError, TypeError):
                    pass
            
            # Логируем ответ с метриками
            log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                request_id=request_id,
                user_ip=user_ip,
                duration_ms=duration_ms,
                request_size_bytes=request_size_bytes,
                response_size_bytes=response_size_bytes
            )
            
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error(
                error=e,
                context=f"Обработка запроса {method} {path}",
                request_id=request_id,
                user_ip=user_ip
            )
            raise

# Подключаем middleware
app.add_middleware(LoggingMiddleware)


@app.on_event("startup")
async def startup_event():
    """Проверка подключения к БД при старте"""
    if not check_connection():
        logger.warning("Database connection failed!")


# ==================== UI Routes ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница - редирект на список"""
    return RedirectResponse(url="/mnt/list")


@app.get("/mnt/create", response_class=HTMLResponse)
async def create_page(request: Request, db: Session = Depends(get_db), error: Optional[str] = None):
    """Страница создания МНТ с предзаполненными дефолтными значениями"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    log_user_action(
        action="Открыта страница создания МНТ",
        user="anonymous",
        request_id=request_id,
        user_ip=user_ip,
        url="/mnt/create"
    )
    
    default_data = get_default_mnt_data()
    return templates.TemplateResponse("create.html", {
        "request": request,
        "data": default_data,
        "error_message": error
    })


@app.get("/mnt/list", response_class=HTMLResponse)
async def list_page(
    request: Request, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    tag_id: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    page: int = 1,
    per_page: int = 20,
    success: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Страница со списком МНТ с пагинацией, фильтрами и сортировкой"""
    skip = (page - 1) * per_page
    documents, total = list_mnt(
        db, 
        search=search,
        status=status,
        author=author,
        tag_id=tag_id,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip, 
        limit=per_page
    )
    
    # Получаем все уникальные теги из всех документов для фильтра
    all_tags_from_db = []
    tags_set = set()
    
    # Извлекаем теги из data_json каждого документа
    for doc in documents:
        # Извлекаем теги из JSONB данных документа
        doc_json = doc.get("data_json", {})
        
        logger.debug(f"Document {doc.get('id')}: data_json type = {type(doc_json)}, keys = {list(doc_json.keys()) if isinstance(doc_json, dict) else 'not a dict'}")
        
        if isinstance(doc_json, dict):
            doc_tags = doc_json.get("tags", [])
            logger.debug(f"Document {doc.get('id')}: tags from data_json = {doc_tags}, type = {type(doc_tags)}")
        else:
            doc_tags = []
            logger.debug(f"Document {doc.get('id')}: data_json is not a dict, setting tags to empty list")
        
        # Добавляем теги в документ для отображения
        if isinstance(doc_tags, list) and doc_tags:
            doc["tags"] = [{"name": tag} for tag in doc_tags if tag]
            logger.debug(f"Document {doc.get('id')}: setting doc['tags'] = {doc['tags']}")
            # Собираем уникальные теги для фильтра
            for tag in doc_tags:
                if tag and isinstance(tag, str) and tag.strip() and tag not in tags_set:
                    tags_set.add(tag)
                    all_tags_from_db.append({"name": tag, "id": tag})
        else:
            doc["tags"] = []
            logger.debug(f"Document {doc.get('id')}: no tags found, setting doc['tags'] = []")
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # Преобразуем коды ошибок в понятные сообщения
    error_messages = {
        "confluence_not_configured": "Не удалось удалить МНТ: Confluence недоступен или не настроен. Проверьте настройки в файле .env. Удаление заблокировано, чтобы не допустить потери данных в Confluence.",
        "already_deleted": "МНТ уже удален.",
        "delete_failed": "Не удалось удалить МНТ. Попробуйте позже.",
        "not_deleted": "МНТ не был удален.",
        "duplicate_failed": "Не удалось продублировать МНТ. Попробуйте позже.",
        "mnt_not_found": "МНТ не найден."
    }
    
    error_message = None
    if error:
        error_message = error_messages.get(error, error)
    
    return templates.TemplateResponse("list.html", {
        "request": request,
        "documents": documents,
        "total": total,
        "search_query": search or "",
        "status_filter": status or "",
        "author_filter": author or "",
        "tag_filter": tag_id or "",
        "tags": all_tags_from_db or [],
        "sort_by": sort_by or "created_at",
        "sort_order": sort_order,
        "current_page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "success_message": success,
        "error_message": error_message
    })


@app.get("/mnt/{mnt_id}/edit", response_class=HTMLResponse)
async def edit_page(
    request: Request, 
    mnt_id: int, 
    success: Optional[str] = None,
    error: Optional[str] = None,
    warning: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Страница редактирования МНТ"""
    try:
        logger.debug(f"Загрузка страницы редактирования для МНТ {mnt_id}")
        document = get_mnt(db, mnt_id)
        if not document:
            logger.warning(f"МНТ {mnt_id} не найден")
            raise HTTPException(status_code=404, detail="МНТ не найден")
        
        logger.debug(f"МНТ {mnt_id} найден, заголовок: {document.get('title')}")
        
        # Получаем список существующих вложений из Confluence (если страница опубликована)
        existing_attachments = []
        if document.get("confluence_page_id"):
            try:
                confluence_client = get_confluence_client()
                existing_attachments = await confluence_client.get_attachments(document["confluence_page_id"])
                logger.debug(f"Получено {len(existing_attachments)} вложений из Confluence")
            except Exception as e:
                # Если не удалось получить вложения, просто игнорируем ошибку
                logger.warning(f"Не удалось получить список вложений: {e}", exc_info=True)
        
        # Убеждаемся, что data_json существует и является словарем
        data_json = document.get("data_json") or {}
        if not isinstance(data_json, dict):
            logger.warning(f"data_json для МНТ {mnt_id} не является словарем, тип: {type(data_json)}")
            data_json = {}
        
        # Логируем теги при загрузке страницы редактирования
        tags_in_data = data_json.get("tags", [])
        logger.info(f"EDIT_PAGE: Загрузка страницы редактирования МНТ {mnt_id}, теги в data_json: {tags_in_data} (тип: {type(tags_in_data)})")
        
        # Проверяем, есть ли неопубликованные изменения (упрощенная проверка по датам)
        has_unpublished_changes = False
        if document.get("status") == "published" and document.get("confluence_page_id"):
            if document.get("last_publish_at") and document.get("updated_at"):
                if document["updated_at"] > document["last_publish_at"]:
                    has_unpublished_changes = True
                    logger.debug(f"МНТ {mnt_id}: Обнаружены неопубликованные изменения (updated_at > last_publish_at)")
                else:
                    logger.debug(f"МНТ {mnt_id}: Нет неопубликованных изменений (updated_at <= last_publish_at)")
            else:
                logger.debug(f"МНТ {mnt_id}: Отсутствует last_publish_at или updated_at")
        else:
            logger.debug(f"МНТ {mnt_id}: Статус не 'published' или нет confluence_page_id")
        
        # Получаем параметры из query string, если не переданы напрямую
        success_message = success or request.query_params.get("success")
        error_message = error or request.query_params.get("error")
        warning_message = warning or request.query_params.get("warning")
        
        return templates.TemplateResponse("edit.html", {
            "request": request,
            "document": document,
            "data": data_json,
            "existing_attachments": existing_attachments,
            "has_unpublished_changes": has_unpublished_changes,
            "success_message": success_message,
            "error_message": error_message,
            "warning_message": warning_message
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы редактирования МНТ {mnt_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


# ==================== Helper Functions for Versions ====================

def create_version_after_save(
    db: Session,
    mnt_id: int,
    document: dict,
    data_json: dict,
    author: str,
    status: str,
    confluence_page_id: Optional[int] = None,
    confluence_page_url: Optional[str] = None,
    last_publish_at: Optional[datetime] = None
) -> Optional[dict]:
    """Создает версию МНТ после сохранения/публикации
    
    Args:
        db: Сессия БД
        mnt_id: ID МНТ документа
        document: Полный объект документа (для получения текущих данных)
        data_json: JSON данные документа
        author: Автор текущего сохранения
        status: Статус версии (draft/published)
        confluence_page_id: ID страницы в Confluence (если опубликована)
        confluence_page_url: URL страницы в Confluence (если опубликована)
        last_publish_at: Дата публикации (если опубликована)
    
    Returns:
        Dict с информацией о созданной версии или None, если версия не была создана
    """
    try:
        # Получаем последнюю версию из таблицы "История изменений"
        latest_version = get_latest_version_from_history(data_json)
        
        if not latest_version:
            # Если версии нет в таблице, не создаем версию (это первое сохранение)
            logger.debug(f"Версия не найдена в таблице 'История изменений' для МНТ {mnt_id}, пропускаем создание версии")
            return None
        
        # ВАЖНО: Используем ТУ ЖЕ версию, что в "Истории изменений", БЕЗ инкремента
        # Версия в mnt.document_versions должна совпадать с версией в "Истории изменений"
        version_number = latest_version
        
        # Проверяем, не существует ли уже версия с таким номером
        # get_document_versions возвращает кортеж (versions, total)
        existing_versions, _ = get_document_versions(db, mnt_id, skip=0, limit=100)
        existing_version_numbers = [v.get("version_number") for v in existing_versions]
        
        if version_number in existing_version_numbers:
            # Версия уже существует, пропускаем создание
            logger.debug(f"Версия {version_number} уже существует для МНТ {mnt_id}, пропускаем создание")
            return None
        
        # Создаем версию
        version_data = create_document_version(
            db=db,
            mnt_id=mnt_id,
            version_number=version_number,
            title=document.get('title', ''),
            project=document.get('project', ''),
            author=author,
            data_json=data_json,
            status=status,
            confluence_space=document.get('confluence_space'),
            confluence_parent_id=document.get('confluence_parent_id'),
            confluence_page_id=confluence_page_id,
            confluence_page_url=confluence_page_url,
            last_publish_at=last_publish_at,
            created_by=author
        )
        
        logger.info(f"Создана версия {version_number} для МНТ {mnt_id} (из 'Истории изменений')")
        return version_data
        
    except Exception as e:
        logger.error(f"Ошибка при создании версии для МНТ {mnt_id}: {e}", exc_info=True)
        # Не прерываем процесс сохранения, если создание версии не удалось
        return None


@app.get("/mnt/{mnt_id}/view", response_class=JSONResponse)
async def view_json(mnt_id: int, db: Session = Depends(get_db)):
    """Просмотр данных МНТ в JSON формате"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    # Преобразуем datetime объекты в строки для JSON сериализации
    def convert_datetime_to_str(obj):
        """Рекурсивно преобразует datetime объекты в строки"""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {key: convert_datetime_to_str(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime_to_str(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(convert_datetime_to_str(item) for item in obj)
        elif isinstance(obj, datetime):
            return obj.isoformat() if obj else None
        elif hasattr(obj, 'isoformat') and callable(getattr(obj, 'isoformat', None)):
            # Проверяем на datetime-like объекты (date, datetime и т.д.)
            try:
                return obj.isoformat()
            except:
                return str(obj)
        elif hasattr(obj, 'strftime') and callable(getattr(obj, 'strftime', None)):
            # Дополнительная проверка на date/datetime объекты
            try:
                return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
            except:
                return str(obj)
        else:
            return obj
    
    # Конвертируем документ
    try:
        serializable_document = convert_datetime_to_str(document)
        return JSONResponse(content=serializable_document)
    except Exception as e:
        logger.error(f"Ошибка сериализации документа {mnt_id} в JSON: {e}", exc_info=True)
        # Альтернативный способ - используем json.dumps с default handler
        try:
            json_str = json.dumps(document, default=str, ensure_ascii=False)
            return JSONResponse(content=json.loads(json_str))
        except Exception as e2:
            logger.error(f"Ошибка альтернативной сериализации: {e2}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ошибка сериализации данных: {str(e2)}")




# ==================== API Routes ====================

@app.post("/api/mnt")
async def api_create_mnt(request: MNTCreateRequest, db: Session = Depends(get_db)):
    """API: Создание нового МНТ"""
    try:
        data_dict = request.data.dict(exclude_none=True)
        confluence_space = data_dict.pop("confluence_space", "")
        confluence_parent_id = data_dict.pop("confluence_parent_id", None)
        
        result = create_mnt(db, data_dict, confluence_space, confluence_parent_id)
        return {"id": result["id"], "message": "МНТ создан успешно"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/mnt")
async def api_list_mnt(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """API: Список МНТ"""
    documents, total = list_mnt(db, skip=skip, limit=limit)
    return {"documents": documents, "total": total}


@app.get("/api/mnt/{mnt_id}")
async def api_get_mnt(mnt_id: int, db: Session = Depends(get_db)):
    """API: Получение МНТ по ID"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    return document


@app.put("/api/mnt/{mnt_id}")
async def api_update_mnt(mnt_id: int, request: MNTUpdateRequest, db: Session = Depends(get_db)):
    """API: Обновление МНТ"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    try:
        data_dict = request.data.dict(exclude_none=True)
        confluence_space = data_dict.pop("confluence_space", "")
        confluence_parent_id = data_dict.pop("confluence_parent_id", None)
        
        success = update_mnt(db, mnt_id, data_dict, confluence_space, confluence_parent_id)
        if not success:
            raise HTTPException(status_code=500, detail="Ошибка обновления")
        
        return {"message": "МНТ обновлен успешно"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/autocomplete/projects")
async def api_autocomplete_projects(db: Session = Depends(get_db)):
    """API: Автодополнение для списка проектов"""
    try:
        result = db.execute(
            text("SELECT DISTINCT project FROM mnt.documents WHERE project IS NOT NULL AND project != '' ORDER BY project")
        ).fetchall()
        projects = [row[0] for row in result if row[0]]
        return projects
    except Exception as e:
        logger.error(f"Ошибка получения списка проектов: {e}", exc_info=True)
        return []


@app.get("/api/autocomplete/authors")
async def api_autocomplete_authors(db: Session = Depends(get_db)):
    """API: Автодополнение для списка авторов"""
    try:
        result = db.execute(
            text("SELECT DISTINCT author FROM mnt.documents WHERE author IS NOT NULL AND author != '' ORDER BY author")
        ).fetchall()
        authors = [row[0] for row in result if row[0]]
        return authors
    except Exception as e:
        logger.error(f"Ошибка получения списка авторов: {e}", exc_info=True)
        return []


@app.get("/api/autocomplete/tags")
async def api_autocomplete_tags(db: Session = Depends(get_db)):
    """API: Автодополнение для списка тегов"""
    try:
        # Получаем все теги из JSONB поля data_json
        result = db.execute(
            text("""
                SELECT DISTINCT jsonb_array_elements_text(data_json->'tags') as tag
                FROM mnt.documents
                WHERE data_json->'tags' IS NOT NULL 
                  AND jsonb_array_length(data_json->'tags') > 0
                ORDER BY tag
            """)
        ).fetchall()
        tags = [row[0] for row in result if row[0] and isinstance(row[0], str) and row[0].strip()]
        return tags
    except Exception as e:
        logger.error(f"Ошибка получения списка тегов: {e}", exc_info=True)
        return []


@app.post("/api/mnt/{mnt_id}/publish")
async def api_publish_mnt(mnt_id: int, db: Session = Depends(get_db)):
    """API: Публикация/обновление МНТ в Confluence"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    try:
        confluence_client = get_confluence_client()
        data = document["data_json"]
        
        # Генерируем контент
        content = render_mnt_to_confluence_storage(data)
        title = data.get("title", document["title"])
        space_key = document.get("confluence_space") or data.get("confluence_space", "")
        
        if not space_key:
            raise HTTPException(status_code=400, detail="Не указан Confluence Space")
        
        parent_id = document.get("confluence_parent_id") or data.get("confluence_parent_id")
        
        # Если страница уже существует - обновляем, иначе создаем
        if document.get("confluence_page_id"):
            # Обновляем существующую страницу
            page_info = await confluence_client.get_page(document["confluence_page_id"])
            current_version = page_info["version"]["number"]
            
            result = await confluence_client.update_page(
                page_id=document["confluence_page_id"],
                title=title,
                content=content,
                version=current_version
            )
        else:
            # Создаем новую страницу
            result = await confluence_client.create_page(
                space_key=space_key,
                title=title,
                content=content,
                parent_id=parent_id
            )
        
        # Обновляем информацию в БД
        update_confluence_info(
            db, mnt_id,
            page_id=result["id"],
            page_url=result["url"],
            status="published"
        )
        
        # Сохраняем версию ПОСЛЕ успешной публикации
        document_data = get_mnt(db, mnt_id)
        if document_data:
            save_version(
                db,
                mnt_id,
                document_data.get("data_json", {}),
                changed_by="unknown",
                change_reason="Версия после успешной публикации в Confluence"
            )
        
        return {
            "message": "МНТ успешно опубликован в Confluence",
            "page_id": result["id"],
            "page_url": result["url"]
        }
    
    except Exception as e:
        # Сохраняем ошибку в БД
        set_error_status(db, mnt_id, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка публикации в Confluence: {str(e)}")


# ==================== Form Handlers ====================

def update_history_changes_table(
    current_history: Optional[str],
    author: str,
    description: str,
    is_first_entry: bool = False
) -> str:
    """
    Обновляет таблицу истории изменений.
    
    Args:
        current_history: Текущая история изменений (может быть None или пустая)
        author: Автор изменений (Фамилия И.О.)
        description: Описание изменений
        is_first_entry: True если это первая запись при создании МНТ
    
    Returns:
        Обновленная история изменений в формате таблицы
    """
    today = datetime.now().strftime("%d.%m.%Y")
    
    if not current_history or not current_history.strip():
        # Создаем первую запись
        version = "0.1"
        if is_first_entry:
            description = description or "Заполнены основные пункты"
        header = "Дата|Версия|Описание|Автор"
        first_entry = f"{today}|{version}|{description}|{author}"
        return f"{header}\n{first_entry}"
    
    # Парсим текущую историю
    lines = current_history.strip().split('\n')
    if len(lines) < 2:
        # Если только заголовок, создаем первую запись
        version = "0.1"
        header = lines[0] if lines else "Дата|Версия|Описание|Автор"
        first_entry = f"{today}|{version}|{description}|{author}"
        return f"{header}\n{first_entry}"
    
    # Находим последнюю версию
    last_version = "0.1"
    version_found = False
    for line in reversed(lines[1:]):  # Пропускаем заголовок
        if '|' in line and line.strip():
            parts = line.split('|')
            if len(parts) >= 2:
                try:
                    version_str = parts[1].strip()
                    version_parts = version_str.split('.')
                    if len(version_parts) == 2:
                        major = int(version_parts[0])
                        minor = int(version_parts[1]) + 1
                        last_version = f"{major}.{minor}"
                        version_found = True
                        break
                except (ValueError, IndexError):
                    continue
    
    # Если версия не найдена, начинаем с 0.2
    if not version_found:
        last_version = "0.2"
    
    # Добавляем новую запись
    new_entry = f"{today}|{last_version}|{description}|{author}"
    return current_history + "\n" + new_entry


@app.post("/mnt/create")
async def handle_create_form(
    request: Request,
    # Заголовок документа
    project_name: str = Form(...),
    organization_name: str = Form(...),
    system_version: str = Form(...),
    author: str = Form(...),  # Для истории изменений
    # Раздел 1: История изменений
    history_changes_table: Optional[str] = Form(None),
    change_description: Optional[str] = Form(None),  # Описание изменений для истории
    # Раздел 2: Лист согласования
    approval_list_table: Optional[str] = Form(None),
    # Раздел 3: Сокращения и терминология
    abbreviations_table: Optional[str] = Form(None),
    terminology_table: Optional[str] = Form(None),
    # Раздел 4: Введение
    introduction_text: Optional[str] = Form(None),
    # Раздел 5: Цели и задачи НТ
    goals_business: Optional[str] = Form(None),
    goals_technical: Optional[str] = Form(None),
    tasks_nt: Optional[str] = Form(None),
    # Раздел 6: Ограничения и риски НТ
    limitations_list: Optional[str] = Form(None),
    risks_table: Optional[str] = Form(None),
    # Раздел 7: Объект НТ
    object_general: Optional[str] = Form(None),
    performance_requirements: Optional[str] = Form(None),
    component_architecture_text: Optional[str] = Form(None),
    component_architecture_image_file: Optional[UploadFile] = File(None),
    information_architecture_image_file: Optional[UploadFile] = File(None),
    # Раздел 8: Тестовый и промышленный стенды
    test_stand_architecture_text: Optional[str] = Form(None),
    stand_comparison_table: Optional[str] = Form(None),
    # Раздел 9: Стратегия тестирования
    planned_tests_intro: Optional[str] = Form(None),
    planned_tests_table: Optional[str] = Form(None),
    planned_tests_note: Optional[str] = Form(None),
    completion_conditions: Optional[str] = Form(None),
    # Раздел 10: Наполнение БД
    database_preparation_text: Optional[str] = Form(None),
    database_preparation_table: Optional[str] = Form(None),
    # Раздел 11: Моделирование нагрузки
    load_modeling_principles: Optional[str] = Form(None),
    load_profiles_intro: Optional[str] = Form(None),
    load_profiles_table: Optional[str] = Form(None),
    use_scenarios_intro: Optional[str] = Form(None),
    use_scenarios_table: Optional[str] = Form(None),
    emulators_description: Optional[str] = Form(None),
    # Раздел 12: Мониторинг
    monitoring_intro: Optional[str] = Form(None),
    monitoring_tools_intro: Optional[str] = Form(None),
    monitoring_tools_table: Optional[str] = Form(None),
    monitoring_tools_note: Optional[str] = Form(None),
    system_resources_intro: Optional[str] = Form(None),
    system_resources_table: Optional[str] = Form(None),
    business_metrics_intro: Optional[str] = Form(None),
    business_metrics_table: Optional[str] = Form(None),
    # Раздел 13: Требования к Заказчику
    customer_requirements_list: Optional[str] = Form(None),
    # Раздел 14: Материалы
    deliverables_intro: Optional[str] = Form(None),
    deliverables_table: Optional[str] = Form(None),
    deliverables_working_docs_table: Optional[str] = Form(None),
    # Раздел 15: Контакты
    contacts_table: Optional[str] = Form(None),
    # Confluence
    confluence_space: str = Form(...),
    confluence_parent_id: Optional[int] = Form(None),
    publish: Optional[str] = Form(None),  # Если есть - публикуем в Confluence
    tags: Optional[str] = Form(None),  # Теги через запятую
    db: Session = Depends(get_db)
):
    """Обработка формы создания МНТ"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    should_publish = publish == "1"
    action_type = "публикация" if should_publish else "создание черновика"
    
    logger.info(
        f"НАЧАЛО СОЗДАНИЯ МНТ | Проект: {project_name} | Автор: {author} | Действие: {action_type}",
        extra={
            'request_id': request_id,
            'user_ip': user_ip,
            'user_name': author
        }
    )
    
    # Обрабатываем пользовательские блоки из формы
    custom_sections = []
    form_data = await request.form()
    
    # Собираем пользовательские блоки
    custom_section_ids = set()
    for key in form_data.keys():
        if key.startswith('custom_sections[') and '][id]' in key:
            # Извлекаем ID из ключа: custom_sections[12345][id] -> 12345
            section_id = key.split('[')[1].split(']')[0]
            custom_section_ids.add(section_id)
    
    for section_id in custom_section_ids:
        section_data = {
            'id': form_data.get(f'custom_sections[{section_id}][id]', section_id),
            'title': form_data.get(f'custom_sections[{section_id}][title]', ''),
            'position': int(form_data.get(f'custom_sections[{section_id}][position]', 15)),
            'text': form_data.get(f'custom_sections[{section_id}][text]', ''),
            'table': form_data.get(f'custom_sections[{section_id}][table]', ''),
            'list': form_data.get(f'custom_sections[{section_id}][list]', '')
        }
        if section_data['title']:  # Добавляем только если есть название
            custom_sections.append(section_data)
    
    # Сортируем по position
    custom_sections.sort(key=lambda x: x['position'])
    
    # Формируем данные согласно новой структуре
    data = {
        "project_name": project_name,
        "organization_name": organization_name,
        "system_version": system_version,
        "history_changes_table": history_changes_table,
        "approval_list_table": approval_list_table,
        "abbreviations_table": abbreviations_table,
        "terminology_table": terminology_table,
        "introduction_text": introduction_text,
        "goals_business": goals_business,
        "goals_technical": goals_technical,
        "tasks_nt": tasks_nt,
        "limitations_list": limitations_list,
        "risks_table": risks_table,
        "object_general": object_general,
        "performance_requirements": performance_requirements,
        "component_architecture_text": component_architecture_text,
        "test_stand_architecture_text": test_stand_architecture_text,
        "stand_comparison_table": stand_comparison_table,
        "planned_tests_intro": planned_tests_intro,
        "planned_tests_table": planned_tests_table,
        "planned_tests_note": planned_tests_note,
        "completion_conditions": completion_conditions,
        "database_preparation_text": database_preparation_text,
        "database_preparation_table": database_preparation_table,
        "load_modeling_principles": load_modeling_principles,
        "load_profiles_intro": load_profiles_intro,
        "load_profiles_table": load_profiles_table,
        "use_scenarios_intro": use_scenarios_intro,
        "use_scenarios_table": use_scenarios_table,
        "emulators_description": emulators_description,
        "monitoring_intro": monitoring_intro,
        "monitoring_tools_intro": monitoring_tools_intro,
        "monitoring_tools_table": monitoring_tools_table,
        "monitoring_tools_note": monitoring_tools_note,
        "system_resources_intro": system_resources_intro,
        "system_resources_table": system_resources_table,
        "business_metrics_intro": business_metrics_intro,
        "business_metrics_table": business_metrics_table,
        "customer_requirements_list": customer_requirements_list,
        "deliverables_intro": deliverables_intro,
        "deliverables_table": deliverables_table,
        "deliverables_working_docs_table": deliverables_working_docs_table,
        "contacts_table": contacts_table,
    }
    
    # Обрабатываем пользовательские блоки из формы
    custom_sections = []
    form_data = await request.form()
    
    # Собираем пользовательские блоки
    custom_section_ids = set()
    for key in form_data.keys():
        if key.startswith('custom_sections[') and '][id]' in key:
            # Извлекаем ID из ключа: custom_sections[12345][id] -> 12345
            section_id = key.split('[')[1].split(']')[0]
            custom_section_ids.add(section_id)
    
    for section_id in custom_section_ids:
        section_data = {
            'id': form_data.get(f'custom_sections[{section_id}][id]', section_id),
            'title': form_data.get(f'custom_sections[{section_id}][title]', ''),
            'position': int(form_data.get(f'custom_sections[{section_id}][position]', 15)),
            'text': form_data.get(f'custom_sections[{section_id}][text]', ''),
            'table': form_data.get(f'custom_sections[{section_id}][table]', ''),
            'list': form_data.get(f'custom_sections[{section_id}][list]', '')
        }
        if section_data['title']:  # Добавляем только если есть название
            custom_sections.append(section_data)
    
    # Сортируем по position
    custom_sections.sort(key=lambda x: x['position'])
    
    # Добавляем custom_sections в data
    data["custom_sections"] = custom_sections if custom_sections else None
    
    # Для совместимости с БД используем project_name как title и project
    title_for_db = project_name
    project_for_db = project_name
    
    # Автоматически обновляем историю изменений при создании МНТ
    # При первом создании всегда создается первая запись
    # Если пользователь не указал описание - используем значение по умолчанию
    change_desc = (change_description.strip() if change_description and change_description.strip() else "Заполнены основные пункты")
    
    # При создании МНТ: если история уже есть в форме (от JavaScript) - используем её как есть
    # НЕ вызываем update_history_changes_table, чтобы не добавить дубликат
    if history_changes_table and history_changes_table.strip():
        # Проверяем, что есть хотя бы заголовок и одна строка данных
        lines = [l.strip() for l in history_changes_table.strip().split('\n') if l.strip()]
        if len(lines) >= 2:
            # Есть заголовок и хотя бы одна строка - используем как есть
            logger.debug(f"CREATE: Используем историю из формы (строк: {len(lines)-1})")
            data["history_changes_table"] = history_changes_table
        else:
            # Только заголовок - создаем первую запись
            logger.debug("CREATE: Только заголовок в форме, создаем первую запись")
            data["history_changes_table"] = update_history_changes_table(
                current_history=None,
                author=author,
                description=change_desc,
                is_first_entry=True
            )
    else:
        # История пуста - создаем первую запись
        logger.debug("CREATE: История пуста, создаем первую запись")
        data["history_changes_table"] = update_history_changes_table(
            current_history=None,
            author=author,
            description=change_desc,
            is_first_entry=True
        )
    
    # Обрабатываем теги - разбиваем строку через запятую и сохраняем как список в JSON
    logger.info(f"CREATE: Получены теги из формы: '{tags}' (тип: {type(tags)}, repr: {repr(tags)})")
    
    # Проверяем, что теги не None и не пустая строка
    tags_str = str(tags).strip() if tags is not None else ""
    if tags_str:
        tag_list = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        if tag_list:
            data["tags"] = tag_list
            logger.info(f"CREATE: Теги из формы успешно обработаны: '{tags}' -> список: {tag_list}")
        else:
            data["tags"] = []
            logger.warning(f"CREATE: Теги из формы '{tags}' не содержат валидных значений, устанавливаем пустой список")
    else:
        data["tags"] = []
        logger.info(f"CREATE: Теги не указаны в форме (tags={repr(tags)}), устанавливаем пустой список")
    
    logger.info(f"CREATE: Словарь data после обработки тегов содержит tags: {data.get('tags', 'NOT FOUND')} (тип: {type(data.get('tags'))})")
    
    # Создаем МНТ в БД (используем старую структуру БД для совместимости)
    try:
        logger.info(
            f"СОЗДАНИЕ МНТ В БД | Проект: {project_for_db} | Название: {title_for_db}",
            extra={
                'request_id': request_id,
                'user_ip': user_ip,
                'user_name': author
            }
        )
        mnt_data_for_db = {
            "title": title_for_db,
            "project": project_for_db,
            "author": author,
            **data  # Все новые данные попадают в data_json, включая теги
        }
        logger.info(f"CREATE: Данные для сохранения включают tags: {mnt_data_for_db.get('tags', 'NOT FOUND')} (тип: {type(mnt_data_for_db.get('tags'))})")
        logger.info(f"CREATE: Полный словарь mnt_data_for_db содержит ключи: {list(mnt_data_for_db.keys())}")
        if "tags" not in mnt_data_for_db:
            logger.error("CREATE: КРИТИЧЕСКАЯ ОШИБКА - теги отсутствуют в mnt_data_for_db!")
        result = create_mnt(db, mnt_data_for_db, confluence_space, confluence_parent_id)
        mnt_id = result["id"]
        
        logger.info(
            f"МНТ УСПЕШНО СОЗДАН | ID: {mnt_id} | Проект: {project_for_db} | Название: {title_for_db}",
            extra={
                'request_id': request_id,
                'user_ip': user_ip,
                'user_name': author
            }
        )
        
        # Логируем действие
        log_mnt_operation("Создание МНТ", mnt_id, author or "unknown", 
                         request_id=request_id, user_ip=user_ip)
        log_action(db, mnt_id, author or "unknown", "created", 
                  f"Создан новый МНТ: {title_for_db}",
                  {"project": project_for_db, "space": confluence_space})
    except Exception as e:
        log_error(e, "Ошибка создания МНТ")
        # Редиректим на страницу создания с сообщением об ошибке
        import urllib.parse
        error_msg = urllib.parse.quote(f"Ошибка создания МНТ: {str(e)[:200]}")
        return RedirectResponse(url=f"/mnt/create?error={error_msg}", status_code=303)
    
    # Если не публикуем - статус уже "draft" (установлен при создании)
    # Если нужно опубликовать в Confluence
    # Проверяем наличие параметра publish (может быть "1", "true", или любое непустое значение)
    logger.debug(f"ПОЛУЧЕННЫЕ ПАРАМЕТРЫ: publish = {publish!r}, type = {type(publish)}")
    
    # Проверяем разные варианты значения publish
    should_publish = False
    if publish is not None:
        publish_str = str(publish).strip()
        should_publish = publish_str and publish_str.lower() not in ("none", "false", "0", "")
        logger.debug(f"Обработка publish: '{publish_str}' -> should_publish = {should_publish}")
    else:
        logger.debug("publish is None - публикация не требуется")
    
    logger.debug(f"ИТОГ: should_publish = {should_publish}")
    logger.debug(f"confluence_space = {confluence_space}, confluence_parent_id = {confluence_parent_id}")
    
    if should_publish:
        try:
            logger.debug(f"Начинаем публикацию МНТ {mnt_id} в Confluence...")
            confluence_client = get_confluence_client()
            logger.debug("Confluence клиент создан успешно")
            
            # Обрабатываем изображения архитектуры
            component_architecture_image_filename = None
            information_architecture_image_filename = None
            other_images = []
            
            if component_architecture_image_file and component_architecture_image_file.filename:
                component_architecture_image_filename = component_architecture_image_file.filename
            
            if information_architecture_image_file and information_architecture_image_file.filename:
                information_architecture_image_filename = information_architecture_image_file.filename
            
            # Генерируем контент
            logger.debug("Генерируем контент для Confluence...")
            content = render_mnt_to_confluence_storage(
                data,
                component_architecture_image=component_architecture_image_filename,
                information_architecture_image=information_architecture_image_filename,
                other_images=other_images
            )
            logger.debug(f"Контент сгенерирован, длина: {len(content)} символов")
            
            # История изменений уже обновлена выше при сохранении (при создании МНТ)
            # Используем текущую историю из data
            
            # Сначала публикуем в Confluence
            logger.debug(f"Вызываем confluence_client.create_page с параметрами:")
            logger.debug(f"  space_key={confluence_space}, title={title_for_db}, parent_id={confluence_parent_id}")
            result_confluence = await confluence_client.create_page(
                space_key=confluence_space,
                title=title_for_db,
                content=content,
                parent_id=confluence_parent_id
            )
            logger.debug(f"Страница создана в Confluence: {result_confluence}")
            
            page_id = result_confluence["id"]
            logger.debug(f"Page ID получен: {page_id}")
            
            # Загружаем изображения архитектуры в Confluence
            if component_architecture_image_file and component_architecture_image_file.filename:
                try:
                    file_content = await component_architecture_image_file.read()
                    content_type = component_architecture_image_file.content_type or mimetypes.guess_type(component_architecture_image_file.filename)[0] or "image/png"
                    await confluence_client.upload_attachment(
                        page_id=page_id,
                        filename=component_architecture_image_file.filename,
                        file_content=file_content,
                        content_type=content_type
                    )
                except Exception as e:
                    logger.error(f"Ошибка загрузки изображения компонентной архитектуры: {e}", exc_info=True)
            
            if information_architecture_image_file and information_architecture_image_file.filename:
                try:
                    file_content = await information_architecture_image_file.read()
                    content_type = information_architecture_image_file.content_type or mimetypes.guess_type(information_architecture_image_file.filename)[0] or "image/png"
                    await confluence_client.upload_attachment(
                        page_id=page_id,
                        filename=information_architecture_image_file.filename,
                        file_content=file_content,
                        content_type=content_type
                    )
                except Exception as e:
                    logger.error(f"Ошибка загрузки изображения информационной архитектуры: {e}", exc_info=True)
            
            # Загружаем изображение max_performance.png для терминологии, если используется термин "Максимальная производительность"
            terminology_table = data.get("terminology_table", "")
            has_max_performance_term = "Максимальная производительность" in terminology_table or "максимальная производительность" in terminology_table.lower()
            if terminology_table and has_max_performance_term:
                try:
                    image_path = Path("app/static/images/max_performance.png")
                    if image_path.exists():
                        with open(image_path, "rb") as f:
                            file_content = f.read()
                        # Проверяем, существует ли уже это изображение в Confluence
                        try:
                            existing_attachments = await confluence_client.get_attachments(page_id)
                            has_max_performance = any(att.get("title") == "max_performance.png" for att in existing_attachments)
                        except:
                            # Если не удалось получить список вложений, предполагаем, что файла нет
                            has_max_performance = False
                        
                        if not has_max_performance:
                            await confluence_client.upload_attachment(
                                page_id=page_id,
                                filename="max_performance.png",
                                file_content=file_content,
                                content_type="image/png"
                            )
                            logger.info("Загружено изображение max_performance.png для терминологии")
                        else:
                            logger.debug("Изображение max_performance.png уже существует в Confluence, пропускаем загрузку")
                    else:
                        logger.warning(f"Файл {image_path} не найден")
                except Exception as e:
                    # Ошибка загрузки изображения не должна блокировать публикацию
                    error_msg = str(e)
                    if "same file name as an existing attachment" in error_msg.lower() or "already exists" in error_msg.lower() or "Cannot add a new attachment with same file name" in error_msg:
                        logger.debug("Изображение max_performance.png уже существует в Confluence, пропускаем загрузку")
                    else:
                        logger.warning(f"Ошибка загрузки изображения max_performance.png (не критично, публикация продолжается): {e}")
            
            # Обновляем данные в БД с новой историей изменений и устанавливаем статус "published"
            update_mnt(db, mnt_id, {
                "title": title_for_db,
                "project": project_for_db,
                "author": author,
                **data
            }, confluence_space, confluence_parent_id, status="published")
            
            # Обновляем информацию о Confluence странице (это дополнительно устанавливает статус и дату публикации)
            update_confluence_info(
                db, mnt_id,
                page_id=page_id,
                page_url=result_confluence["url"],
                status="published"
            )
            logger.info(f"Успешно опубликовано в Confluence. МНТ ID: {mnt_id}, Page ID: {page_id}")
            # Логируем успешную публикацию
            log_action(db, mnt_id, author or "unknown", "published", 
                      f"МНТ опубликован в Confluence. Page ID: {page_id}",
                      {"page_id": page_id, "page_url": result_confluence["url"], "space": confluence_space})
            
            # ВЕРСИЯ СОЗДАЕТСЯ ТОЛЬКО ПОСЛЕ УСПЕШНОГО ЗАВЕРШЕНИЯ ВСЕХ ОПЕРАЦИЙ ПУБЛИКАЦИИ
            # Получаем обновленный документ после публикации для создания версии
            document_after_publish = get_mnt(db, mnt_id)
            if document_after_publish:
                # Создаем версию после успешной публикации
                create_version_after_save(
                    db=db,
                    mnt_id=mnt_id,
                    document=document_after_publish,
                    data_json=document_after_publish.get("data_json", {}),
                    author=author,
                    status="published",
                    confluence_page_id=page_id,
                    confluence_page_url=result_confluence["url"],
                    last_publish_at=datetime.now()
                )
        except Exception as e:
            # Сохраняем ошибку в БД
            error_msg = str(e)
            set_error_status(db, mnt_id, error_msg)
            log_error(e, f"Ошибка публикации МНТ {mnt_id} в Confluence")
            logger.error(f"Ошибка публикации МНТ {mnt_id}: {error_msg}", exc_info=True)
            # Логируем ошибку публикации
            log_action(db, mnt_id, author or "unknown", "publish_failed", 
                      f"Ошибка публикации в Confluence: {error_msg[:200]}",
                      {"error": error_msg[:500]})
            # Редиректим на страницу редактирования, чтобы пользователь увидел ошибку
            import urllib.parse
            error_encoded = urllib.parse.quote(error_msg[:200])
            return RedirectResponse(url=f"/mnt/{mnt_id}/edit?error={error_encoded}", status_code=303)
    
    # Редирект на список после успешного создания
    logger.info(
        f"ЗАВЕРШЕНО СОЗДАНИЕ МНТ | ID: {mnt_id} | Статус: {'опубликован' if should_publish else 'черновик'}",
        extra={
            'request_id': request_id,
            'user_ip': user_ip,
            'user_name': author
        }
    )
    
    if should_publish:
        return RedirectResponse(url=f"/mnt/list?success=created_published&id={mnt_id}", status_code=303)
    else:
        return RedirectResponse(url=f"/mnt/list?success=draft_created&id={mnt_id}", status_code=303)


@app.post("/mnt/{mnt_id}/edit")
async def handle_edit_form(
    request: Request,
    mnt_id: int,
    # Заголовок документа
    project_name: str = Form(...),
    organization_name: str = Form(...),
    system_version: str = Form(...),
    author: str = Form(...),  # Для истории изменений
    # Раздел 1: История изменений
    history_changes_table: Optional[str] = Form(None),
    change_description: Optional[str] = Form(None),  # Описание изменений для истории
    # Раздел 2: Лист согласования
    approval_list_table: Optional[str] = Form(None),
    # Раздел 3: Сокращения и терминология
    abbreviations_table: Optional[str] = Form(None),
    terminology_table: Optional[str] = Form(None),
    # Раздел 4: Введение
    introduction_text: Optional[str] = Form(None),
    # Раздел 5: Цели и задачи НТ
    goals_business: Optional[str] = Form(None),
    goals_technical: Optional[str] = Form(None),
    tasks_nt: Optional[str] = Form(None),
    # Раздел 6: Ограничения и риски НТ
    limitations_list: Optional[str] = Form(None),
    risks_table: Optional[str] = Form(None),
    # Раздел 7: Объект НТ
    object_general: Optional[str] = Form(None),
    performance_requirements: Optional[str] = Form(None),
    component_architecture_text: Optional[str] = Form(None),
    component_architecture_image_file: Optional[UploadFile] = File(None),
    information_architecture_image_file: Optional[UploadFile] = File(None),
    # Раздел 8: Тестовый и промышленный стенды
    test_stand_architecture_text: Optional[str] = Form(None),
    stand_comparison_table: Optional[str] = Form(None),
    # Раздел 9: Стратегия тестирования
    planned_tests_intro: Optional[str] = Form(None),
    planned_tests_table: Optional[str] = Form(None),
    planned_tests_note: Optional[str] = Form(None),
    completion_conditions: Optional[str] = Form(None),
    # Раздел 10: Наполнение БД
    database_preparation_text: Optional[str] = Form(None),
    database_preparation_table: Optional[str] = Form(None),
    # Раздел 11: Моделирование нагрузки
    load_modeling_principles: Optional[str] = Form(None),
    load_profiles_intro: Optional[str] = Form(None),
    load_profiles_table: Optional[str] = Form(None),
    use_scenarios_intro: Optional[str] = Form(None),
    use_scenarios_table: Optional[str] = Form(None),
    emulators_description: Optional[str] = Form(None),
    # Раздел 12: Мониторинг
    monitoring_intro: Optional[str] = Form(None),
    monitoring_tools_intro: Optional[str] = Form(None),
    monitoring_tools_table: Optional[str] = Form(None),
    monitoring_tools_note: Optional[str] = Form(None),
    system_resources_intro: Optional[str] = Form(None),
    system_resources_table: Optional[str] = Form(None),
    business_metrics_intro: Optional[str] = Form(None),
    business_metrics_table: Optional[str] = Form(None),
    # Раздел 13: Требования к Заказчику
    customer_requirements_list: Optional[str] = Form(None),
    # Раздел 14: Материалы
    deliverables_intro: Optional[str] = Form(None),
    deliverables_table: Optional[str] = Form(None),
    deliverables_working_docs_table: Optional[str] = Form(None),
    # Раздел 15: Контакты
    contacts_table: Optional[str] = Form(None),
    # Confluence
    confluence_space: str = Form(...),
    confluence_parent_id: Optional[int] = Form(None),
    publish: Optional[str] = Form(None),  # Если есть - публикуем в Confluence
    tags: Optional[str] = Form(None),  # Теги через запятую
    db: Session = Depends(get_db)
):
    """Обработка формы редактирования МНТ"""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    user_ip = getattr(request.state, 'user_ip', '-')
    
    should_publish = publish == "1"
    action_type = "публикация" if should_publish else "сохранение изменений"
    
    logger.info(
        f"НАЧАЛО РЕДАКТИРОВАНИЯ МНТ | ID: {mnt_id} | Автор: {author} | Действие: {action_type}",
        extra={
            'request_id': request_id,
            'user_ip': user_ip,
            'user_name': author
        }
    )
    
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    # Обрабатываем пользовательские блоки из формы
    custom_sections = []
    form_data = await request.form()
    
    # Собираем пользовательские блоки
    custom_section_ids = set()
    for key in form_data.keys():
        if key.startswith('custom_sections[') and '][id]' in key:
            section_id = key.split('[')[1].split(']')[0]
            custom_section_ids.add(section_id)
    
    for section_id in custom_section_ids:
        section_data = {
            'id': form_data.get(f'custom_sections[{section_id}][id]', section_id),
            'title': form_data.get(f'custom_sections[{section_id}][title]', ''),
            'position': int(form_data.get(f'custom_sections[{section_id}][position]', 15)),
            'text': form_data.get(f'custom_sections[{section_id}][text]', ''),
            'table': form_data.get(f'custom_sections[{section_id}][table]', ''),
            'list': form_data.get(f'custom_sections[{section_id}][list]', '')
        }
        if section_data['title']:
            custom_sections.append(section_data)
    
    # Сортируем по position
    custom_sections.sort(key=lambda x: x['position'])
    
    # Формируем данные согласно новой структуре
    data = {
        "project_name": project_name,
        "organization_name": organization_name,
        "system_version": system_version,
        "history_changes_table": history_changes_table,
        "approval_list_table": approval_list_table,
        "abbreviations_table": abbreviations_table,
        "terminology_table": terminology_table,
        "introduction_text": introduction_text,
        "goals_business": goals_business,
        "goals_technical": goals_technical,
        "tasks_nt": tasks_nt,
        "limitations_list": limitations_list,
        "risks_table": risks_table,
        "object_general": object_general,
        "performance_requirements": performance_requirements,
        "component_architecture_text": component_architecture_text,
        "test_stand_architecture_text": test_stand_architecture_text,
        "stand_comparison_table": stand_comparison_table,
        "planned_tests_intro": planned_tests_intro,
        "planned_tests_table": planned_tests_table,
        "planned_tests_note": planned_tests_note,
        "completion_conditions": completion_conditions,
        "database_preparation_text": database_preparation_text,
        "database_preparation_table": database_preparation_table,
        "load_modeling_principles": load_modeling_principles,
        "load_profiles_intro": load_profiles_intro,
        "load_profiles_table": load_profiles_table,
        "use_scenarios_intro": use_scenarios_intro,
        "use_scenarios_table": use_scenarios_table,
        "emulators_description": emulators_description,
        "monitoring_intro": monitoring_intro,
        "monitoring_tools_intro": monitoring_tools_intro,
        "monitoring_tools_table": monitoring_tools_table,
        "monitoring_tools_note": monitoring_tools_note,
        "system_resources_intro": system_resources_intro,
        "system_resources_table": system_resources_table,
        "business_metrics_intro": business_metrics_intro,
        "business_metrics_table": business_metrics_table,
        "customer_requirements_list": customer_requirements_list,
        "deliverables_intro": deliverables_intro,
        "deliverables_table": deliverables_table,
        "deliverables_working_docs_table": deliverables_working_docs_table,
        "contacts_table": contacts_table,
    }
    
    # Обрабатываем пользовательские блоки из формы
    custom_sections = []
    form_data = await request.form()
    
    # Собираем пользовательские блоки
    custom_section_ids = set()
    for key in form_data.keys():
        if key.startswith('custom_sections[') and '][id]' in key:
            section_id = key.split('[')[1].split(']')[0]
            custom_section_ids.add(section_id)
    
    for section_id in custom_section_ids:
        section_data = {
            'id': form_data.get(f'custom_sections[{section_id}][id]', section_id),
            'title': form_data.get(f'custom_sections[{section_id}][title]', ''),
            'position': int(form_data.get(f'custom_sections[{section_id}][position]', 15)),
            'text': form_data.get(f'custom_sections[{section_id}][text]', ''),
            'table': form_data.get(f'custom_sections[{section_id}][table]', ''),
            'list': form_data.get(f'custom_sections[{section_id}][list]', '')
        }
        if section_data['title']:
            custom_sections.append(section_data)
    
    # Сортируем по position
    custom_sections.sort(key=lambda x: x['position'])
    
    # Добавляем custom_sections в data
    data["custom_sections"] = custom_sections if custom_sections else None
    
    # Получаем документ до изменений (нужно сделать это раньше, так как используется ниже)
    document_before = get_mnt(db, mnt_id)
    
    # Обрабатываем теги - разбиваем строку через запятую и сохраняем как список в JSON
    # При редактировании: если теги не указаны в форме, сохраняем существующие из БД
    logger.debug(f"EDIT: Получены теги из формы: '{tags}' (тип: {type(tags)})")
    if tags is not None and str(tags).strip():
        tag_list = [tag.strip() for tag in str(tags).split(',') if tag.strip()]
        data["tags"] = tag_list
        logger.info(f"EDIT: Теги из формы: '{tags}' -> список: {tag_list}")
    else:
        # Если теги не указаны - сохраняем существующие из БД (если они есть)
        existing_tags = []
        if document_before and isinstance(document_before.get("data_json"), dict):
            existing_tags = document_before.get("data_json", {}).get("tags", [])
            if isinstance(existing_tags, list):
                logger.debug(f"EDIT: Теги не указаны в форме, сохраняем существующие из БД: {existing_tags}")
            else:
                existing_tags = []
                logger.warning(f"EDIT: Существующие теги в БД не являются списком: {type(existing_tags)}")
        data["tags"] = existing_tags
        logger.debug(f"EDIT: Используем существующие теги из БД: {existing_tags}")
    
    # Для совместимости с БД используем project_name как title и project
    title_for_db = project_name
    project_for_db = project_name
    
    # Определяем, нужно ли публиковать
    should_publish = publish and str(publish).strip() and str(publish).strip() != "None"
    logger.debug(f"EDIT: publish parameter = {publish}, should_publish = {should_publish}")
    
    # Обновляем историю изменений при редактировании
    # Проверяем изменения в данных (если еще не проверили выше)
    if document_before:
        # Проверка уже выполнена выше при сохранении версии, используем тот же результат
        if 'has_data_changes' not in locals():
            old_data = document_before.get("data_json", {})
            changes = compare_mnt_data(old_data, data)
            has_data_changes = len(changes) > 0
    else:
        has_data_changes = False
    
    # Обновляем историю изменений
    form_history = history_changes_table or ""
    old_history = document_before.get("data_json", {}).get("history_changes_table", "") or "" if document_before else ""
    
    if form_history and form_history.strip():
        form_lines = [l.strip() for l in form_history.strip().split('\n') if l.strip() and '|' in l]
        old_lines = [l.strip() for l in old_history.strip().split('\n') if l.strip() and '|' in l] if old_history else []
        
        # Если в форме больше строк - значит пользователь добавил новую строку
        if len(form_lines) > len(old_lines):
            data["history_changes_table"] = form_history
        else:
            # История не изменилась - используем старую историю или из формы
            data["history_changes_table"] = old_history or form_history or ""
    else:
        # История из формы пуста - используем старую историю
        data["history_changes_table"] = old_history or ""
    
    # Получаем текущий статус МНТ
    current_status = document_before.get("status") if document_before else None
    
    # Определяем, какой статус устанавливать
    # При явном сохранении без публикации: устанавливаем "draft"
    # При публикации: статус установим после успешной публикации (None = не менять сейчас)
    if should_publish:
        # Публикация - статус установим после успешной публикации
        status_to_set = None
        logger.debug(f"EDIT: Публикация - статус будет установлен после успешной публикации")
    else:
        # Явное сохранение без публикации - устанавливаем "draft"
        status_to_set = "draft"
        logger.debug(f"EDIT: Явное сохранение без публикации - устанавливаем статус 'draft'")
    
    # Обновляем МНТ в БД
    mnt_data_for_update = {
        "title": title_for_db,
        "project": project_for_db,
        "author": author,
        **data  # Все новые данные попадают в data_json, включая теги
    }
    logger.debug(f"EDIT: Данные для обновления включают tags: {mnt_data_for_update.get('tags', 'NOT FOUND')}")
    update_mnt(db, mnt_id, mnt_data_for_update, confluence_space, confluence_parent_id, status=status_to_set)
    
    log_mnt_operation("Обновление МНТ", mnt_id, author or "unknown")
    
    # Вычисляем изменения
    old_data = document_before.get("data_json", {}) if document_before else {}
    new_data = data
    changes = compare_mnt_data(old_data, new_data)
    
    # Формируем описание изменений
    if changes:
        changes_summary = f"Изменено полей: {len(changes)}"
        changes_details = {change["field"]: {
            "field_name": change["field_name"],
            "type": change["type"],
            "old": str(change.get("old", ""))[:200] if change.get("old") else None,
            "new": str(change.get("new", ""))[:200] if change.get("new") else None
        } for change in changes[:50]}  # Ограничиваем до 50 изменений
    else:
        changes_summary = "Изменений не обнаружено"
        changes_details = {}
    
    # Логируем обновление с деталями изменений
    log_action(db, mnt_id, author or "unknown", "updated", 
              f"МНТ обновлен: {title_for_db}. {changes_summary}",
              {
                  "project": project_for_db,
                  "changes_count": len(changes),
                  "changes": changes_details
              })
    
    # Если нужно опубликовать/обновить в Confluence
    if should_publish:
        try:
            confluence_client = get_confluence_client()
            
            # Получаем существующие вложения из Confluence
            existing_attachments = []
            component_architecture_image_filename = None
            information_architecture_image_filename = None
            
            if document.get("confluence_page_id"):
                try:
                    existing_attachments_list = await confluence_client.get_attachments(document["confluence_page_id"])
                    for att in existing_attachments_list:
                        existing_attachments.append(att.get("filename"))
                        # Проверяем, есть ли уже загруженные изображения архитектуры
                        filename = att.get("filename", "")
                        if "component_architecture" in filename.lower() or "компонентная" in filename.lower():
                            component_architecture_image_filename = filename
                        elif "information_architecture" in filename.lower() or "информационная" in filename.lower():
                            information_architecture_image_filename = filename
                except Exception as e:
                    logger.warning(f"Не удалось получить существующие вложения: {e}", exc_info=True)
            
            # Обрабатываем новые изображения архитектуры
            if component_architecture_image_file and component_architecture_image_file.filename:
                component_architecture_image_filename = component_architecture_image_file.filename
            
            if information_architecture_image_file and information_architecture_image_file.filename:
                information_architecture_image_filename = information_architecture_image_file.filename
            
            # История изменений уже обновлена выше при сохранении
            # При публикации используем текущую историю из data
            
            # Генерируем контент
            content = render_mnt_to_confluence_storage(
                data,
                component_architecture_image=component_architecture_image_filename,
                information_architecture_image=information_architecture_image_filename,
                other_images=None
            )
            
            if document.get("confluence_page_id"):
                # Обновляем существующую страницу
                page_info = await confluence_client.get_page(document["confluence_page_id"])
                current_version = page_info["version"]["number"]
                
                result_confluence = await confluence_client.update_page(
                    page_id=document["confluence_page_id"],
                    title=title_for_db,
                    content=content,
                    version=current_version
                )
                page_id = result_confluence["id"]
            else:
                # Создаем новую страницу
                result_confluence = await confluence_client.create_page(
                    space_key=confluence_space,
                    title=title_for_db,
                    content=content,
                    parent_id=confluence_parent_id
                )
                page_id = result_confluence["id"]
            
            # Загружаем новые изображения архитектуры в Confluence
            if component_architecture_image_file and component_architecture_image_file.filename:
                try:
                    file_content = await component_architecture_image_file.read()
                    content_type = component_architecture_image_file.content_type or mimetypes.guess_type(component_architecture_image_file.filename)[0] or "image/png"
                    await confluence_client.upload_attachment(
                        page_id=page_id,
                        filename=component_architecture_image_file.filename,
                        file_content=file_content,
                        content_type=content_type
                    )
                except Exception as e:
                    logger.error(f"Ошибка загрузки изображения компонентной архитектуры: {e}", exc_info=True)
            
            if information_architecture_image_file and information_architecture_image_file.filename:
                try:
                    file_content = await information_architecture_image_file.read()
                    content_type = information_architecture_image_file.content_type or mimetypes.guess_type(information_architecture_image_file.filename)[0] or "image/png"
                    await confluence_client.upload_attachment(
                        page_id=page_id,
                        filename=information_architecture_image_file.filename,
                        file_content=file_content,
                        content_type=content_type
                    )
                except Exception as e:
                    logger.error(f"Ошибка загрузки изображения информационной архитектуры: {e}", exc_info=True)
            
            # Загружаем изображение max_performance.png для терминологии, если используется термин "Максимальная производительность"
            terminology_table = data.get("terminology_table", "")
            has_max_performance_term = "Максимальная производительность" in terminology_table or "максимальная производительность" in terminology_table.lower()
            if terminology_table and has_max_performance_term:
                try:
                    image_path = Path("app/static/images/max_performance.png")
                    if image_path.exists():
                        with open(image_path, "rb") as f:
                            file_content = f.read()
                        # Проверяем, существует ли уже это изображение в Confluence
                        try:
                            existing_attachments = await confluence_client.get_attachments(page_id)
                            has_max_performance = any(att.get("title") == "max_performance.png" for att in existing_attachments)
                        except:
                            # Если не удалось получить список вложений, предполагаем, что файла нет
                            has_max_performance = False
                        
                        if not has_max_performance:
                            await confluence_client.upload_attachment(
                                page_id=page_id,
                                filename="max_performance.png",
                                file_content=file_content,
                                content_type="image/png"
                            )
                            logger.info("Загружено изображение max_performance.png для терминологии")
                        else:
                            logger.debug("Изображение max_performance.png уже существует в Confluence, пропускаем загрузку")
                    else:
                        logger.warning(f"Файл {image_path} не найден")
                except Exception as e:
                    # Ошибка загрузки изображения не должна блокировать публикацию
                    error_msg = str(e)
                    if "same file name as an existing attachment" in error_msg.lower() or "already exists" in error_msg.lower() or "Cannot add a new attachment with same file name" in error_msg:
                        logger.debug("Изображение max_performance.png уже существует в Confluence, пропускаем загрузку")
                    else:
                        logger.warning(f"Ошибка загрузки изображения max_performance.png (не критично, публикация продолжается): {e}")
            
            # Обновляем данные в БД с новой историей изменений и устанавливаем статус "published"
            update_mnt(db, mnt_id, {
                "title": title_for_db,
                "project": project_for_db,
                "author": author,
                **data
            }, confluence_space, confluence_parent_id, status="published")
            
            # Обновляем информацию о Confluence странице (это дополнительно устанавливает статус и дату публикации)
            update_confluence_info(
                db, mnt_id,
                page_id=page_id,
                page_url=result_confluence["url"],
                status="published"
            )
            
            logger.info(f"EDIT: Успешно опубликовано в Confluence. МНТ ID: {mnt_id}, Page ID: {page_id}")
            # Логируем успешную публикацию
            log_action(db, mnt_id, author or "unknown", "published", 
                      f"МНТ обновлен в Confluence. Page ID: {page_id}",
                      {"page_id": page_id, "page_url": result_confluence["url"], "space": confluence_space})
            
            # ВЕРСИЯ СОЗДАЕТСЯ ТОЛЬКО ПОСЛЕ УСПЕШНОГО ЗАВЕРШЕНИЯ ВСЕХ ОПЕРАЦИЙ ПУБЛИКАЦИИ
            # Получаем обновленный документ после публикации для создания версии
            document_after_publish = get_mnt(db, mnt_id)
            if document_after_publish:
                # Создаем версию после успешной публикации
                create_version_after_save(
                    db=db,
                    mnt_id=mnt_id,
                    document=document_after_publish,
                    data_json=document_after_publish.get("data_json", {}),
                    author=author,
                    status="published",
                    confluence_page_id=page_id,
                    confluence_page_url=result_confluence["url"],
                    last_publish_at=datetime.now()
                )
        except Exception as e:
            error_msg = str(e)
            set_error_status(db, mnt_id, error_msg)
            logger.error(f"EDIT: Ошибка публикации МНТ {mnt_id}: {error_msg}", exc_info=True)
            # Логируем ошибку публикации
            log_action(db, mnt_id, author or "unknown", "publish_failed", 
                      f"Ошибка публикации в Confluence: {error_msg[:200]}",
                      {"error": error_msg[:500]})
            # Редирект с ошибкой
            import urllib.parse
            error_encoded = urllib.parse.quote(error_msg[:200])
            return RedirectResponse(url=f"/mnt/{mnt_id}/edit?error={error_encoded}", status_code=303)
    
    # Редирект с сообщением об успехе
    if should_publish:
        return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=updated_published", status_code=303)
    else:
        return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=updated", status_code=303)


@app.get("/mnt/{mnt_id}/attachment/{attachment_id}/delete", response_class=RedirectResponse)
async def delete_attachment(mnt_id: int, attachment_id: int, db: Session = Depends(get_db)):
    """Удаление вложения из Confluence"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    if not document.get("confluence_page_id"):
        raise HTTPException(status_code=400, detail="Страница не опубликована в Confluence")
    
    try:
        confluence_client = get_confluence_client()
        await confluence_client.delete_attachment(document["confluence_page_id"], attachment_id)
        log_mnt_operation("Удаление вложения", mnt_id, details={"attachment_id": attachment_id})
    except Exception as e:
        log_error(e, f"Ошибка удаления вложения МНТ #{mnt_id}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении вложения: {str(e)}")
    
    return RedirectResponse(url=f"/mnt/{mnt_id}/edit", status_code=303)


@app.get("/mnt/{mnt_id}/preview", response_class=HTMLResponse)
async def preview_mnt(mnt_id: int, db: Session = Depends(get_db)):
    """Превью МНТ перед публикацией"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    try:
        data = document.get("data_json", {})
        content = render_mnt_to_confluence_storage(data)
        
        # Простой HTML превью
        html_preview = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Превью МНТ - {document.get('title', '')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .preview-header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="preview-header">
        <h1>Превью МНТ</h1>
        <p><strong>Проект:</strong> {document.get('project', '')}</p>
        <p><a href="/mnt/{mnt_id}/edit">← Вернуться к редактированию</a></p>
    </div>
    <div style="border: 1px solid #ddd; padding: 20px; background: white;">
        <pre style="white-space: pre-wrap; font-family: inherit;">{content[:5000]}...</pre>
        <p><em>Это упрощенный превью. Полный контент будет отображаться в Confluence.</em></p>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_preview)
    except Exception as e:
        log_error(e, f"Ошибка создания превью МНТ #{mnt_id}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания превью: {str(e)}")


@app.get("/mnt/{mnt_id}/export/{format}")
async def export_mnt(mnt_id: int, format: str, db: Session = Depends(get_db)):
    """Экспорт МНТ в различных форматах"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    try:
        data = document.get("data_json", {})
        
        if format == "html":
            content = export_to_html(data)
            return Response(content=content, media_type="text/html", 
                          headers={"Content-Disposition": f'attachment; filename="mnt_{mnt_id}.html"'})
        elif format == "txt":
            content = export_to_text(data)
            return Response(content=content, media_type="text/plain",
                          headers={"Content-Disposition": f'attachment; filename="mnt_{mnt_id}.txt"'})
        else:
            raise HTTPException(status_code=400, detail=f"Неподдерживаемый формат: {format}")
    except Exception as e:
        log_error(e, f"Ошибка экспорта МНТ #{mnt_id} в формате {format}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@app.get("/api/mnt/{mnt_id}/completeness")
async def get_mnt_completeness(mnt_id: int, db: Session = Depends(get_db)):
    """Получить информацию о полноте заполнения МНТ"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    try:
        data = document.get("data_json", {})
        completeness = check_document_completeness(data)
        return JSONResponse(content=completeness)
    except Exception as e:
        log_error(e, f"Ошибка проверки полноты МНТ #{mnt_id}")
        raise HTTPException(status_code=500, detail=f"Ошибка проверки полноты: {str(e)}")


@app.post("/api/mnt/completeness")
async def check_completeness_from_data(request: Request, db: Session = Depends(get_db)):
    """Проверить полноту заполнения на основе переданных данных формы"""
    try:
        form_data = await request.form()
        data = {}
        
        # Собираем все данные из формы
        for key, value in form_data.items():
            if key not in ["confluence_space", "confluence_parent_id", "publish"]:
                data[key] = value
        
        completeness = check_document_completeness(data)
        return JSONResponse(content=completeness)
    except Exception as e:
        log_error(e, "Ошибка проверки полноты из данных формы")
        raise HTTPException(status_code=500, detail=f"Ошибка проверки полноты: {str(e)}")


@app.get("/api/tag-templates")
async def list_tag_templates():
    """Получить список всех доступных шаблонов для тегов"""
    try:
        templates = get_available_templates()
        return JSONResponse(content=templates)
    except Exception as e:
        log_error(e, "Ошибка получения списка шаблонов тегов")
        raise HTTPException(status_code=500, detail=f"Ошибка получения шаблонов: {str(e)}")


@app.post("/api/tag-templates/apply")
async def apply_tag_templates(request: Request):
    """Применить шаблоны данных на основе тегов"""
    try:
        body = await request.json()
        tags = body.get("tags", [])
        current_data = body.get("current_data", {})
        overwrite = body.get("overwrite", False)
        
        if not tags:
            return JSONResponse(content=current_data)
        
        # Применяем шаблоны
        updated_data = apply_template_to_data(current_data, tags, overwrite)
        return JSONResponse(content=updated_data)
    except Exception as e:
        log_error(e, "Ошибка применения шаблонов тегов")
        raise HTTPException(status_code=500, detail=f"Ошибка применения шаблонов: {str(e)}")




@app.get("/api/tags")
async def list_tags(db: Session = Depends(get_db)):
    """Получение списка всех тегов"""
    tags = get_tags(db)
    return {"tags": tags}


@app.post("/api/tags")
async def create_new_tag(name: str = Form(...), color: str = Form("#6c757d"), db: Session = Depends(get_db)):
    """Создание нового тега"""
    try:
        tag = create_tag(db, name, color)
        return {"success": True, "tag": tag}
    except Exception as e:
        log_error(e, "Ошибка создания тега")
        raise HTTPException(status_code=500, detail=f"Ошибка создания тега: {str(e)}")


@app.post("/mnt/{mnt_id}/tags")
async def update_document_tags(mnt_id: int, tag_ids: str = Form(""), db: Session = Depends(get_db)):
    """Обновление тегов документа"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    tag_id_list = [int(tid) for tid in tag_ids.split(",") if tid.strip() and tid.strip().isdigit()] if tag_ids else []
    set_document_tags(db, mnt_id, tag_id_list)
    
    log_mnt_operation("Обновление тегов", mnt_id)
    
    return RedirectResponse(url=f"/mnt/{mnt_id}/edit", status_code=303)


@app.get("/admin/audit/export")
async def export_audit_logs(
    request: Request,
    mnt_id: Optional[int] = Query(None),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db)
):
    """Экспорт логов аудита (истории действий)"""
    try:
        # Получаем историю действий
        if mnt_id:
            history = get_action_history(db, mnt_id, limit=10000)
            filename = f"audit_logs_mnt_{mnt_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            # Для всех МНТ нужен отдельный запрос
            query = text("""
                SELECT ah.id, ah.mnt_id, ah.user_name, ah.action_type, 
                       ah.action_description, ah.details, ah.created_at,
                       d.title as mnt_title
                FROM mnt.action_history ah
                LEFT JOIN mnt.documents d ON ah.mnt_id = d.id
                ORDER BY ah.created_at DESC
                LIMIT 10000
            """)
            result = db.execute(query)
            rows = result.fetchall()
            
            history = []
            for row in rows:
                details_value = row[5]
                if details_value:
                    if isinstance(details_value, dict):
                        details_dict = details_value
                    else:
                        details_dict = json.loads(details_value) if details_value else {}
                else:
                    details_dict = {}
                
                history.append({
                    "id": row[0],
                    "mnt_id": row[1],
                    "user_name": row[2],
                    "action_type": row[3],
                    "action_description": row[4],
                    "details": details_dict,
                    "created_at": row[6],
                    "mnt_title": row[7]
                })
            filename = f"audit_logs_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "csv":
            # Экспорт в CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                "ID", "МНТ ID", "Название МНТ", "Дата/Время", 
                "Пользователь", "Тип действия", "Описание", "Детали"
            ])
            
            # Данные
            for item in history:
                writer.writerow([
                    item.get("id", ""),
                    item.get("mnt_id", ""),
                    item.get("mnt_title", ""),
                    item.get("created_at").strftime('%Y-%m-%d %H:%M:%S') if item.get("created_at") else "",
                    item.get("user_name", ""),
                    item.get("action_type", ""),
                    item.get("action_description", ""),
                    json.dumps(item.get("details", {}), ensure_ascii=False)
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content.encode('utf-8-sig'),  # UTF-8 BOM для Excel
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.csv"'
                }
            )
        
        elif format == "json":
            # Экспорт в JSON
            json_content = json.dumps(history, ensure_ascii=False, indent=2, default=str)
            
            return Response(
                content=json_content.encode('utf-8'),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.json"'
                }
            )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта логов аудита: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@app.post("/api/log/client")
async def log_from_client(request: Request):
    """API для логирования сообщений от клиента (браузера)"""
    try:
        data = await request.json()
        level = data.get("level", "INFO").upper()
        message = data.get("message", "")
        context = data.get("context", {})
        
        # Формируем полное сообщение
        context_str = ""
        if context:
            context_parts = [f"{k}={v}" for k, v in context.items()]
            context_str = f" | {' | '.join(context_parts)}"
        
        full_message = f"[CLIENT]{context_str} {message}"
        
        # Логируем в зависимости от уровня
        if level == "DEBUG":
            logger.debug(full_message)
        elif level == "INFO":
            logger.info(full_message)
        elif level == "WARNING" or level == "WARN":
            logger.warning(full_message)
        elif level == "ERROR":
            logger.error(full_message)
        else:
            logger.info(full_message)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Ошибка при логировании из клиента: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.post("/mnt/{mnt_id}/delete", response_class=RedirectResponse)
async def delete_mnt(mnt_id: int, db: Session = Depends(get_db)):
    """Удаление МНТ (soft delete)"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    if document.get("deleted_at"):
        # Уже удален
        return RedirectResponse(url="/mnt/list?error=already_deleted", status_code=303)
    
    # Проверяем доступность Confluence, если есть опубликованная страница
    confluence_page_id = document.get("confluence_page_id")
    if confluence_page_id:
        if not is_confluence_configured():
            # Confluence недоступен, но есть опубликованная страница - блокируем удаление
            logger.warning(
                f"Попытка удаления МНТ {mnt_id} с confluence_page_id={confluence_page_id}, "
                f"но Confluence credentials не настроены. Удаление заблокировано."
            )
            return RedirectResponse(
                url="/mnt/list?error=confluence_not_configured", 
                status_code=303
            )
    
    try:
        # Удаляем страницу из Confluence, если она была опубликована
        if confluence_page_id:
            try:
                confluence_client = get_confluence_client()
                await confluence_client.delete_page(confluence_page_id)
                logger.info(f"Страница {confluence_page_id} удалена из Confluence для МНТ {mnt_id}")
            except ValueError as e:
                # Confluence credentials not configured (не должно быть, т.к. проверили выше)
                logger.error(f"Confluence credentials не настроены для удаления МНТ {mnt_id}: {e}")
                return RedirectResponse(
                    url="/mnt/list?error=confluence_not_configured", 
                    status_code=303
                )
            except Exception as e:
                # Если страница уже удалена или другая ошибка - продолжаем soft delete в БД
                logger.warning(f"Не удалось удалить страницу из Confluence для МНТ {mnt_id}: {e}")
        
        # Мягкое удаление в БД
        soft_delete_mnt(db, mnt_id)
        
        # Логируем действие
        log_action(
            db, mnt_id, 
            document.get("author", "unknown"), 
            "deleted",
            f"МНТ удален (soft delete). Страница Confluence {'удалена' if confluence_page_id else 'не была опубликована'}",
            {"confluence_page_id": confluence_page_id}
        )
        
        return RedirectResponse(url="/mnt/list?success=deleted", status_code=303)
    except Exception as e:
        logger.error(f"Ошибка удаления МНТ {mnt_id}: {e}", exc_info=True)
        return RedirectResponse(url=f"/mnt/list?error=delete_failed&id={mnt_id}", status_code=303)


@app.post("/mnt/{mnt_id}/restore", response_class=RedirectResponse)
async def restore_mnt_endpoint(mnt_id: int, db: Session = Depends(get_db)):
    """Восстановление удаленного МНТ"""
    document = get_mnt_with_deleted(db, mnt_id, include_deleted=True)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    if not document.get("deleted_at"):
        # Не удален
        return RedirectResponse(url="/mnt/list?error=not_deleted", status_code=303)
    
    try:
        # Восстанавливаем запись в БД
        restore_mnt(db, mnt_id)
        
        # Пересоздаем страницу в Confluence, если она была опубликована до удаления
        # (используем сохраненные данные на момент удаления)
        if document.get("confluence_space") and document.get("data_json"):
            try:
                confluence_client = get_confluence_client()
                data = document.get("data_json", {})
                
                # Получаем title для страницы
                title = data.get("title") or document.get("title") or f"МНТ {mnt_id}"
                
                # Генерируем контент
                from app.render import render_mnt_to_confluence_storage
                content = render_mnt_to_confluence_storage(data)
                
                # Создаем новую страницу
                result = await confluence_client.create_page(
                    space_key=document["confluence_space"],
                    title=title,
                    content=content,
                    parent_id=document.get("confluence_parent_id")
                )
                
                # Обновляем информацию о Confluence
                update_confluence_info(
                    db, mnt_id,
                    page_id=result["id"],
                    page_url=result["url"],
                    status="published"
                )
                
                logger.info(f"МНТ {mnt_id} восстановлен, страница {result['id']} пересоздана в Confluence")
                
                # Логируем действие
                log_action(
                    db, mnt_id,
                    document.get("author", "unknown"),
                    "restored",
                    f"МНТ восстановлен. Страница Confluence пересоздана (новый ID: {result['id']})",
                    {"new_page_id": result["id"], "old_page_id": document.get("confluence_page_id")}
                )
                
                return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=restored", status_code=303)
            except Exception as e:
                # Если не удалось пересоздать в Confluence - все равно восстанавливаем в БД
                logger.error(f"Ошибка пересоздания страницы в Confluence для МНТ {mnt_id}: {e}", exc_info=True)
                
                # Логируем действие (без пересоздания страницы)
                log_action(
                    db, mnt_id,
                    document.get("author", "unknown"),
                    "restored",
                    f"МНТ восстановлен в БД, но не удалось пересоздать страницу в Confluence: {str(e)[:200]}",
                    {"error": str(e)[:500]}
                )
                
                return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=restored&warning=confluence_failed", status_code=303)
        else:
            # Не было опубликовано - просто восстанавливаем
            log_action(
                db, mnt_id,
                document.get("author", "unknown"),
                "restored",
                "МНТ восстановлен (не был опубликован в Confluence)",
                {}
            )
            
            return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=restored", status_code=303)
    except Exception as e:
        logger.error(f"Ошибка восстановления МНТ {mnt_id}: {e}", exc_info=True)
        return RedirectResponse(url=f"/mnt/trash?error=restore_failed&id={mnt_id}", status_code=303)


@app.post("/mnt/{mnt_id}/duplicate", response_class=RedirectResponse)
async def duplicate_mnt_endpoint(mnt_id: int, request: Request, db: Session = Depends(get_db)):
    """Дублирование МНТ - создание копии как черновика"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        # Получаем оригинальный МНТ
        original = get_mnt(db, mnt_id)
        if not original:
            return RedirectResponse(url="/mnt/list?error=mnt_not_found", status_code=303)
        
        log_user_action(
            action=f"Дублирование МНТ {mnt_id}",
            user="anonymous",
            request_id=request_id,
            user_ip=user_ip,
            url=f"/mnt/{mnt_id}/duplicate"
        )
        
        # Копируем данные из data_json, исключая историю изменений и лист согласования
        original_data = original.get("data_json", {})
        if not isinstance(original_data, dict):
            original_data = {}
        
        # Создаем копию данных, исключая служебные поля
        new_data = {}
        for key, value in original_data.items():
            # Не копируем историю изменений и лист согласования
            if key not in ["history_changes_table", "approval_list_table"]:
                new_data[key] = value
        
        # Изменяем название, добавляя " (копия)"
        new_title = f"{original.get('title', 'МНТ')} (копия)"
        new_data["title"] = new_title
        
        # Копируем project и author из оригинала
        new_data["project"] = original.get("project", "")
        new_data["author"] = original.get("author", "")
        
        # Сохраняем теги (они уже должны быть в data_json)
        # Теги копируются автоматически, так как они в data_json
        
        # Копируем confluence_space и confluence_parent_id (но не page_id)
        confluence_space = original.get("confluence_space")
        confluence_parent_id = original.get("confluence_parent_id")
        
        # Создаем новый МНТ как черновик
        result = create_mnt(
            db=db,
            data=new_data,
            confluence_space=confluence_space or "TEST",
            confluence_parent_id=confluence_parent_id
        )
        
        new_mnt_id = result["id"]
        
        # Логируем действие
        log_action(
            db=db,
            mnt_id=new_mnt_id,
            user_name=original.get("author", "unknown"),
            action_type="duplicate",
            action_description=f"Создана копия МНТ из оригинала #{mnt_id}",
            details={
                "original_mnt_id": mnt_id,
                "original_title": original.get("title"),
                "new_title": new_title
            }
        )
        
        log_mnt_operation(
            operation="duplicate",
            mnt_id=new_mnt_id,
            details=f"Скопирован из МНТ {mnt_id}",
            request_id=request_id,
            user_ip=user_ip
        )
        
        return RedirectResponse(url=f"/mnt/list?success=duplicated&new_id={new_mnt_id}", status_code=303)
        
    except Exception as e:
        logger.error(f"Ошибка дублирования МНТ {mnt_id}: {e}", exc_info=True)
        return RedirectResponse(url=f"/mnt/list?error=duplicate_failed&id={mnt_id}", status_code=303)


@app.get("/mnt/trash", response_class=HTMLResponse)
async def trash_page(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("deleted_at"),
    sort_order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db)
):
    """Страница корзины с удаленными МНТ"""
    # Получаем список удаленных МНТ
    documents, total = list_mnt(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        include_deleted=True  # Показываем только удаленные
    )
    
    return templates.TemplateResponse("trash.html", {
        "request": request,
        "documents": documents,
        "total": total,
        "skip": skip,
        "limit": limit,
        "search_query": search or "",
        "sort_by": sort_by or "deleted_at",
        "sort_order": sort_order or "desc",
        "success_message": request.query_params.get("success"),
        "error_message": request.query_params.get("error")
    })


@app.post("/api/log-js-error")
async def log_js_error(request: Request):
    """Endpoint для логирования JavaScript ошибок с клиента"""
    try:
        # Получаем данные из тела запроса (JSON)
        try:
            body = await request.json()
            error_message = body.get("error_message") or "Unknown error"
            error_source = body.get("error_source") or "Unknown"
            error_line = body.get("error_line") or "Unknown"
            error_col = body.get("error_col") or "Unknown"
            error_stack = body.get("error_stack") or "No stack trace"
            user_agent = body.get("user_agent") or "Unknown"
            url = body.get("url") or "Unknown"
        except Exception as json_err:
            # Если не JSON, пытаемся получить из Form данных
            try:
                form_data = await request.form()
                error_message = form_data.get("error_message", "Unknown error")
                error_source = form_data.get("error_source", "Unknown")
                error_line = form_data.get("error_line", "Unknown")
                error_col = form_data.get("error_col", "Unknown")
                error_stack = form_data.get("error_stack", "No stack trace")
                user_agent = form_data.get("user_agent", "Unknown")
                url = form_data.get("url", "Unknown")
            except:
                error_message = "Failed to parse error data"
                error_source = "Unknown"
                error_line = "Unknown"
                error_col = "Unknown"
                error_stack = f"JSON parse error: {str(json_err)}"
                user_agent = request.headers.get("user-agent", "Unknown")
                url = str(request.url)
        
        # Получаем IP и другие данные из request
        user_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, 'request_id', None) if hasattr(request, 'state') else 'no-request-id'
        
        # Формируем детальное сообщение об ошибке
        error_details = {
            "message": error_message or "Unknown error",
            "source": error_source or "Unknown",
            "line": error_line or "Unknown",
            "column": error_col or "Unknown",
            "stack": error_stack or "No stack trace",
            "url": url or str(request.url),
            "user_agent": user_agent or request.headers.get("user-agent", "Unknown")
        }
        
        # Логируем ошибку
        log_error(
            error_type="JavaScript Error",
            error_message=f"JS Error: {error_details['message']}",
            error_details=error_details,
            request_id=request_id,
            user_ip=user_ip
        )
        
        logger.error(
            f"JavaScript ошибка на клиенте: {error_details['message']}",
            extra={
                'request_id': request_id,
                'user_ip': user_ip,
                'error_source': error_details['source'],
                'error_line': error_details['line'],
                'error_url': error_details['url']
            }
        )
        
        return JSONResponse({"status": "logged"})
    except Exception as e:
        logger.exception(f"Ошибка при логировании JS ошибки: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/upload-terminology-image")


# ==================== Version History Routes ====================

@app.get("/mnt/{mnt_id}/versions", response_class=HTMLResponse)
async def versions_page(
    request: Request,
    mnt_id: int,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """Страница истории версий МНТ"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    # Получаем версии с пагинацией (10 на страницу)
    per_page = 10
    skip = (page - 1) * per_page
    versions, total = get_document_versions(db, mnt_id, skip=skip, limit=per_page)
    
    # Получаем все версии для выпадающего списка сравнения (без пагинации)
    all_versions, _ = get_document_versions(db, mnt_id, skip=0, limit=1000)
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return templates.TemplateResponse("versions.html", {
        "request": request,
        "document": document,
        "versions": versions,
        "all_versions": all_versions,  # Все версии для выпадающего списка
        "total": total,
        "current_page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    })


@app.get("/mnt/{mnt_id}/compare", response_class=HTMLResponse)
async def compare_versions_direct(
    request: Request,
    mnt_id: int,
    version1_id: str = Query(...),
    version2_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Прямое сравнение двух версий МНТ (через форму выбора)"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    # Получаем первую версию
    try:
        version1_id_int = int(version1_id)
        version1 = get_document_version(db, version1_id_int)
        if not version1:
            raise HTTPException(status_code=404, detail="Первая версия не найдена")
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный ID первой версии")
    
    # Определяем вторую версию для сравнения
    compare_with_current = False
    if not version2_id:
        raise HTTPException(status_code=400, detail="Необходимо выбрать вторую версию для сравнения")
    
    # Сравниваем с другой сохраненной версией
    try:
        version2_id_int = int(version2_id)
        version2 = get_document_version(db, version2_id_int)
        if not version2:
            raise HTTPException(status_code=404, detail="Вторая версия не найдена")
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный ID второй версии")
    
    # Выполняем сравнение
    diff_result = compare_versions(version1, version2)
    
    return templates.TemplateResponse("version_compare.html", {
        "request": request,
        "document": document,
        "version1": version1,
        "version2": version2,
        "diff_result": diff_result,
        "compare_with_current": compare_with_current
    })


@app.get("/mnt/{mnt_id}/versions/{version_id}/compare", response_class=HTMLResponse)
async def compare_version_page(
    request: Request,
    mnt_id: int,
    version_id: int,
    compare_with_current: bool = Query(False),
    compare_with_version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Страница сравнения версий МНТ"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    version1 = get_document_version(db, version_id)
    if not version1:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    
    # Определяем вторую версию для сравнения
    if compare_with_current:
        # Сравниваем с текущим состоянием
        version2 = document
    elif compare_with_version_id:
        # Сравниваем с другой версией
        version2 = get_document_version(db, compare_with_version_id)
        if not version2:
            raise HTTPException(status_code=404, detail="Вторая версия не найдена")
    else:
        # По умолчанию сравниваем с текущим состоянием
        version2 = document
        compare_with_current = True
    
    # Выполняем сравнение
    diff_result = compare_versions(version1, version2)
    
    return templates.TemplateResponse("version_compare.html", {
        "request": request,
        "document": document,
        "version1": version1,
        "version2": version2,
        "diff_result": diff_result,
        "compare_with_current": compare_with_current
    })


@app.post("/mnt/{mnt_id}/versions/{version_id}/restore", response_class=RedirectResponse)
async def restore_version(
    request: Request,
    mnt_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """Восстановление версии МНТ"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    
    version = get_document_version(db, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    
    # Восстанавливаем данные из версии (без изменения таблицы "История изменений")
    restored_data = {
        "title": version["title"],
        "project": version["project"],
        "author": version["author"],
        **version["data_json"]
    }
    
    # НЕ добавляем запись в таблицу "История изменений" при восстановлении
    # Пользователь может вручную добавить запись, если необходимо
    
    # Обновляем МНТ восстановленными данными
    update_mnt(
        db, mnt_id,
        restored_data,
        document.get("confluence_space", ""),
        document.get("confluence_parent_id"),
        status="draft"  # Восстановленная версия всегда становится черновиком
    )
    
    # Логируем восстановление
    log_action(
        db, mnt_id,
        version.get("created_by", "unknown"),
        "version_restored",
        f"Восстановлена версия {version['version_number']}",
        {"version_id": version_id, "version_number": version["version_number"]}
    )
    
    return RedirectResponse(url=f"/mnt/{mnt_id}/edit?success=version_restored", status_code=303)


@app.post("/api/upload-terminology-image")
async def upload_terminology_image(
    request: Request,
    file: UploadFile = File(...)
):
    """Endpoint для загрузки изображений терминологии"""
    try:
        # Проверяем, что это изображение
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse(
                {"status": "error", "message": "Файл должен быть изображением"},
                status_code=400
            )
        
        # Создаем папку для загрузок, если её нет
        upload_dir = Path("app/static/uploads/terminology")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Возвращаем путь для использования в статических файлах
        static_path = f"/static/uploads/terminology/{unique_filename}"
        
        logger.info(f"Загружено изображение терминологии: {static_path}")
        
        return JSONResponse({
            "status": "success",
            "path": static_path,
            "filename": unique_filename
        })
    except Exception as e:
        logger.exception(f"Ошибка при загрузке изображения терминологии: {e}")
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )
