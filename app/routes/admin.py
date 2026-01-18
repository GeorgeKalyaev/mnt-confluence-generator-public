"""Административные роуты (теги, аудит, логи)"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import JSONResponse, Response
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import json
import io
import csv
from datetime import datetime

# Core
from app.core import get_db

# Services
from app.services import (
    get_tags, create_tag,
    log_action, get_action_history
)

# Utils
from app.utils import (
    log_error, logger
)

# Импортируем templates
templates = Jinja2Templates(directory="app/templates")

# Создаем роутер для административных функций
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/audit/export")
async def export_audit_logs(
    request: Request,
    mnt_id: Optional[int] = Query(None),
    format: str = Query("csv", pattern="^(csv|json)$"),
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
                    item.get("created_at", "").isoformat() if item.get("created_at") else "",
                    item.get("user_name", ""),
                    item.get("action_type", ""),
                    item.get("action_description", ""),
                    json.dumps(item.get("details", {}), ensure_ascii=False)
                ])
            
            content = output.getvalue()
            output.close()
            
            return Response(
                content=content,
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
            )
        else:
            # Экспорт в JSON
            # Конвертируем datetime в строки
            for item in history:
                if isinstance(item.get("created_at"), datetime):
                    item["created_at"] = item["created_at"].isoformat()
            
            return JSONResponse(
                content=history,
                headers={"Content-Disposition": f"attachment; filename={filename}.json"}
            )
    except Exception as e:
        log_error(e, "Ошибка экспорта логов аудита")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


# Добавляем API роуты для тегов в admin роутер (для удобства, но с префиксом /api)
api_admin_router = APIRouter(prefix="/api", tags=["Admin"])


@api_admin_router.get("/tags")
async def list_tags(db: Session = Depends(get_db)):
    """Получение списка всех тегов"""
    tags = get_tags(db)
    return {"tags": tags}


@api_admin_router.post("/tags")
async def create_new_tag(name: str = Form(...), color: str = Form("#6c757d"), db: Session = Depends(get_db)):
    """Создание нового тега"""
    try:
        tag = create_tag(db, name, color)
        return {"success": True, "tag": tag}
    except Exception as e:
        log_error(e, "Ошибка создания тега")
        raise HTTPException(status_code=500, detail=f"Ошибка создания тега: {str(e)}")
