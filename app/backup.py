"""Модуль для резервного копирования базы данных"""
import os
import subprocess
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from app.config import settings
from app.logger import logger

# Создаем директорию для бэкапов
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)


def create_database_backup(output_file: Optional[str] = None) -> str:
    """Создание дампа базы данных PostgreSQL
    
    Args:
        output_file: Путь к файлу бэкапа. Если None, будет создан автоматически.
    
    Returns:
        Путь к созданному файлу бэкапа
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = BACKUP_DIR / f"mnt_db_backup_{timestamp}.sql"
    else:
        output_file = Path(output_file)
    
    # Команда pg_dump
    cmd = [
        "pg_dump",
        "-h", settings.database_host,
        "-p", str(settings.database_port),
        "-U", settings.database_user,
        "-d", settings.database_name,
        "-F", "c",  # Custom format (сжатый)
        "-f", str(output_file),
        "--no-owner",
        "--no-acl"
    ]
    
    # Устанавливаем пароль через переменную окружения
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.database_password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"База данных успешно сохранена в {output_file}")
        return str(output_file)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Ошибка при создании бэкапа БД: {e.stderr}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except FileNotFoundError:
        error_msg = "pg_dump не найден. Убедитесь, что PostgreSQL утилиты установлены."
        logger.error(error_msg)
        raise Exception(error_msg)


def restore_database_backup(backup_file: str, drop_existing: bool = False) -> bool:
    """Восстановление базы данных из бэкапа
    
    Args:
        backup_file: Путь к файлу бэкапа
        drop_existing: Удалить существующую базу данных перед восстановлением
    
    Returns:
        True если восстановление успешно
    """
    backup_file = Path(backup_file)
    
    if not backup_file.exists():
        raise FileNotFoundError(f"Файл бэкапа не найден: {backup_file}")
    
    # Команда pg_restore
    cmd = [
        "pg_restore",
        "-h", settings.database_host,
        "-p", str(settings.database_port),
        "-U", settings.database_user,
        "-d", settings.database_name,
        "-v",  # Verbose
        str(backup_file)
    ]
    
    if drop_existing:
        cmd.append("--clean")
        cmd.append("--if-exists")
    
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.database_password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"База данных успешно восстановлена из {backup_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Ошибка при восстановлении БД: {e.stderr}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except FileNotFoundError:
        error_msg = "pg_restore не найден. Убедитесь, что PostgreSQL утилиты установлены."
        logger.error(error_msg)
        raise Exception(error_msg)


def export_all_data(output_file: Optional[str] = None) -> str:
    """Экспорт всех данных МНТ в JSON архив
    
    Args:
        output_file: Путь к выходному файлу. Если None, будет создан автоматически.
    
    Returns:
        Путь к созданному файлу архива
    """
    from app.database import get_db
    from app.db_operations import list_mnt
    
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = BACKUP_DIR / f"mnt_data_export_{timestamp}.zip"
    else:
        output_file = Path(output_file)
    
    db = next(get_db())
    
    try:
        # Получаем все МНТ (включая удаленные)
        all_mnt, total = list_mnt(db, skip=0, limit=10000, include_deleted=True)
        
        # Собираем данные для экспорта
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_documents": total,
            "documents": []
        }
        
        for mnt in all_mnt:
            export_data["documents"].append({
                "id": mnt.get("id"),
                "title": mnt.get("title"),
                "project": mnt.get("project"),
                "author": mnt.get("author"),
                "created_at": mnt.get("created_at").isoformat() if mnt.get("created_at") else None,
                "updated_at": mnt.get("updated_at").isoformat() if mnt.get("updated_at") else None,
                "status": mnt.get("status"),
                "data_json": mnt.get("data_json"),
                "confluence_space": mnt.get("confluence_space"),
                "confluence_page_id": mnt.get("confluence_page_id"),
                "confluence_page_url": mnt.get("confluence_page_url"),
                "last_publish_at": mnt.get("last_publish_at").isoformat() if mnt.get("last_publish_at") else None,
                "deleted_at": mnt.get("deleted_at").isoformat() if mnt.get("deleted_at") else None
            })
        
        # Создаем ZIP архив с JSON файлом
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # JSON файл с данными
            json_data = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
            zipf.writestr("mnt_data.json", json_data.encode('utf-8'))
            
            # Метаданные экспорта
            metadata = {
                "export_date": datetime.now().isoformat(),
                "total_documents": total,
                "version": "1.0"
            }
            zipf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        
        logger.info(f"Все данные МНТ экспортированы в {output_file} ({total} документов)")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных: {str(e)}")
        raise
    finally:
        db.close()


def list_backups() -> List[Dict[str, Any]]:
    """Получение списка всех бэкапов
    
    Returns:
        Список словарей с информацией о бэкапах
    """
    backups = []
    
    for file_path in BACKUP_DIR.glob("*.sql"):
        stat = file_path.stat()
        backups.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "type": "database"
        })
    
    for file_path in BACKUP_DIR.glob("*.zip"):
        stat = file_path.stat()
        backups.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "type": "data_export"
        })
    
    # Сортируем по дате создания (новые первыми)
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    
    return backups


def delete_backup(backup_file: str) -> bool:
    """Удаление файла бэкапа
    
    Args:
        backup_file: Путь к файлу бэкапа
    
    Returns:
        True если удаление успешно
    """
    backup_file = Path(backup_file)
    
    if not backup_file.exists():
        raise FileNotFoundError(f"Файл бэкапа не найден: {backup_file}")
    
    if not str(backup_file).startswith(str(BACKUP_DIR)):
        raise ValueError("Нельзя удалять файлы вне директории backups")
    
    try:
        backup_file.unlink()
        logger.info(f"Бэкап удален: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении бэкапа: {str(e)}")
        raise
