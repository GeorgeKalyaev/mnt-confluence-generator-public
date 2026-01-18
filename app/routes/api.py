"""REST API роуты для работы с МНТ"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile, Query
from fastapi.responses import JSONResponse, FileResponse
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import json
from pathlib import Path
import uuid
from datetime import datetime

# Core
from app.core import get_db, MNTCreateRequest, MNTUpdateRequest

# Services
from app.services import (
    create_mnt, get_mnt, update_mnt, list_mnt,
    update_confluence_info, set_error_status,
    get_confluence_client,
    render_mnt_to_confluence_storage,
    get_template_data_for_tags, get_available_templates, apply_template_to_data,
    create_database_backup, restore_database_backup, export_all_data,
    list_backups, delete_backup
)

# Utils
from app.utils import (
    log_error, log_user_action, logger, generate_request_id, log_security_event,
    check_document_completeness,
    NotFoundError, SecurityError
)

# Импортируем templates из main
from starlette.templating import Jinja2Templates
templates = Jinja2Templates(directory="app/templates")

# Создаем роутер для API
router = APIRouter(prefix="/api", tags=["API"])


@router.post("/mnt")
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


@router.get("/mnt")
async def api_list_mnt(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """API: Список МНТ"""
    documents, total = list_mnt(db, skip=skip, limit=limit)
    return {"documents": documents, "total": total}


@router.get("/mnt/{mnt_id}")
async def api_get_mnt(mnt_id: int, db: Session = Depends(get_db)):
    """API: Получение МНТ по ID"""
    document = get_mnt(db, mnt_id)
    if not document:
        raise HTTPException(status_code=404, detail="МНТ не найден")
    return document


@router.put("/mnt/{mnt_id}")
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


@router.get("/autocomplete/projects")
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


@router.get("/autocomplete/authors")
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


@router.get("/autocomplete/tags")
async def api_autocomplete_tags(db: Session = Depends(get_db)):
    """API: Автодополнение для списка тегов"""
    try:
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


@router.post("/mnt/{mnt_id}/publish")
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
        
        return {
            "message": "МНТ успешно опубликован в Confluence",
            "page_id": result["id"],
            "page_url": result["url"]
        }
    
    except Exception as e:
        # Сохраняем ошибку в БД
        set_error_status(db, mnt_id, str(e))
        raise HTTPException(status_code=500, detail=f"Ошибка публикации в Confluence: {str(e)}")


@router.get("/mnt/{mnt_id}/completeness")
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


@router.post("/mnt/completeness")
async def check_completeness_from_data(request: Request, db: Session = Depends(get_db)):
    """Проверить полноту заполнения на основе переданных данных формы"""
    try:
        form_data = await request.form()
        data = {}
        
        # Собираем все данные из формы (включая confluence_space и confluence_parent_id для проверки полноты)
        for key, value in form_data.items():
            if key not in ["publish"]:  # Исключаем только publish
                # Сохраняем как строку, убираем лишние пробелы
                data[key] = value.strip() if isinstance(value, str) else value
        
        # Логируем для отладки
        logger.debug(f"Completeness check: received {len(data)} fields, keys: {list(data.keys())[:10]}")
        
        completeness = check_document_completeness(data)
        return JSONResponse(content=completeness)
    except Exception as e:
        log_error(e, "Ошибка проверки полноты из данных формы")
        raise HTTPException(status_code=500, detail=f"Ошибка проверки полноты: {str(e)}")


@router.get("/tag-templates")
async def list_tag_templates():
    """Получить список всех доступных шаблонов для тегов"""
    try:
        templates_list = get_available_templates()
        return JSONResponse(content=templates_list)
    except Exception as e:
        log_error(e, "Ошибка получения списка шаблонов тегов")
        raise HTTPException(status_code=500, detail=f"Ошибка получения шаблонов: {str(e)}")


@router.post("/tag-templates/apply")
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


@router.post("/log/client")
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


@router.post("/log-js-error")
async def log_js_error(request: Request):
    """Endpoint для логирования JavaScript ошибок с клиента"""
    try:
        try:
            body = await request.json()
            error_message = body.get("error_message") or "Unknown error"
            error_source = body.get("error_source") or "Unknown"
            error_line = body.get("error_line") or "Unknown"
            error_col = body.get("error_col") or "Unknown"
            error_stack = body.get("error_stack") or "No stack trace"
            user_agent = body.get("user_agent") or "Unknown"
            url = body.get("url") or "Unknown"
        except Exception:
            form_data = await request.form()
            error_message = form_data.get("error_message", "Unknown error")
            error_source = form_data.get("error_source", "Unknown")
            error_line = form_data.get("error_line", "Unknown")
            error_col = form_data.get("error_col", "Unknown")
            error_stack = form_data.get("error_stack", "No stack trace")
            user_agent = form_data.get("user_agent", "Unknown")
            url = form_data.get("url", "Unknown")
        
        user_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, 'request_id', None) if hasattr(request, 'state') else 'no-request-id'
        
        error_details = {
            "message": error_message or "Unknown error",
            "source": error_source or "Unknown",
            "line": error_line or "Unknown",
            "column": error_col or "Unknown",
            "stack": error_stack or "No stack trace",
            "url": url or str(request.url),
            "user_agent": user_agent or request.headers.get("user-agent", "Unknown")
        }
        
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


@router.post("/upload-terminology-image")
async def upload_terminology_image(request: Request, file: UploadFile = File(...)):
    """Endpoint для загрузки изображений терминологии"""
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            return JSONResponse(
                {"status": "error", "message": "Файл должен быть изображением"},
                status_code=400
            )
        
        upload_dir = Path("app/static/uploads/terminology")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
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


@router.post("/backup/create")
async def create_backup_endpoint(request: Request):
    """Создание бэкапа базы данных"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        backup_file = create_database_backup()
        log_user_action(
            "Создан бэкап базы данных",
            "anonymous",
            {"backup_file": backup_file},
            request_id=request_id,
            user_ip=user_ip,
            url="/api/backup/create"
        )
        return JSONResponse({
            "status": "success",
            "message": "Бэкап успешно создан",
            "backup_file": backup_file
        })
    except Exception as e:
        log_error(error=e, context="create_backup", request_id=request_id, user_ip=user_ip)
        return JSONResponse(
            {"status": "error", "message": f"Ошибка при создании бэкапа: {str(e)}"},
            status_code=500
        )


@router.post("/backup/export-data")
async def export_data_endpoint(request: Request):
    """Экспорт всех данных МНТ в архив"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        export_file = export_all_data()
        log_user_action(
            "Экспортированы все данные МНТ",
            "anonymous",
            {"export_file": export_file},
            request_id=request_id,
            user_ip=user_ip,
            url="/api/backup/export-data"
        )
        return JSONResponse({
            "status": "success",
            "message": "Данные успешно экспортированы",
            "export_file": export_file
        })
    except Exception as e:
        log_error(error=e, context="export_data", request_id=request_id, user_ip=user_ip)
        return JSONResponse(
            {"status": "error", "message": f"Ошибка при экспорте данных: {str(e)}"},
            status_code=500
        )


@router.get("/backup/list")
async def list_backups_endpoint(request: Request):
    """Получение списка всех бэкапов"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        backups = list_backups()
        for backup in backups:
            if isinstance(backup.get("created_at"), datetime):
                backup["created_at"] = backup["created_at"].isoformat()
        
        return JSONResponse({"status": "success", "backups": backups})
    except Exception as e:
        log_error(error=e, context="list_backups", request_id=request_id, user_ip=user_ip)
        return JSONResponse(
            {"status": "error", "message": f"Ошибка при получении списка бэкапов: {str(e)}"},
            status_code=500
        )


@router.post("/backup/restore")
async def restore_backup_endpoint(
    request: Request,
    backup_file: str = Form(...),
    drop_existing: bool = Form(False)
):
    """Восстановление базы данных из бэкапа"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        backup_path = Path("backups") / backup_file
        
        log_security_event(
            event_type="database_restore",
            description=f"Восстановление базы данных из бэкапа: {backup_file}",
            severity="critical",
            details={"backup_file": backup_file, "drop_existing": drop_existing},
            request_id=request_id,
            user_ip=user_ip,
            url="/api/backup/restore"
        )
        
        restore_database_backup(str(backup_path), drop_existing=drop_existing)
        log_user_action(
            "Восстановлена база данных из бэкапа",
            "anonymous",
            {"backup_file": backup_file, "drop_existing": drop_existing},
            request_id=request_id,
            user_ip=user_ip,
            url="/api/backup/restore"
        )
        return JSONResponse({
            "status": "success",
            "message": "База данных успешно восстановлена"
        })
    except Exception as e:
        log_error(error=e, context="restore_backup", request_id=request_id, user_ip=user_ip)
        return JSONResponse(
            {"status": "error", "message": f"Ошибка при восстановлении: {str(e)}"},
            status_code=500
        )


@router.delete("/backup/{backup_filename:path}")
async def delete_backup_endpoint(request: Request, backup_filename: str):
    """Удаление файла бэкапа"""
    request_id = getattr(request.state, 'request_id', '-')
    user_ip = getattr(request.state, 'user_ip', '-')
    
    try:
        backup_path = Path("backups") / backup_filename
        
        if not backup_path.exists():
            raise NotFoundError(f"Файл бэкапа не найден: {backup_filename}")
        
        if not str(backup_path.resolve()).startswith(str(Path("backups").resolve())):
            raise SecurityError("Недопустимый путь к файлу бэкапа")
        
        delete_backup(str(backup_path))
        log_user_action(
            "Удален файл бэкапа",
            "anonymous",
            {"backup_file": backup_filename},
            request_id=request_id,
            user_ip=user_ip,
            url=f"/api/backup/{backup_filename}"
        )
        return JSONResponse({"status": "success", "message": "Бэкап успешно удален"})
    except (NotFoundError, SecurityError) as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=404 if isinstance(e, NotFoundError) else 403
        )
    except Exception as e:
        log_error(error=e, context="delete_backup", request_id=request_id, user_ip=user_ip)
        return JSONResponse(
            {"status": "error", "message": f"Ошибка при удалении бэкапа: {str(e)}"},
            status_code=500
        )
