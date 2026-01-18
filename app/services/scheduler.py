"""Планировщик для автоматических задач (бэкапы, очистка)"""
import asyncio
from datetime import datetime, time
from typing import Optional
import logging

from app.services.backup import create_database_backup, delete_backup, list_backups
from app.core.config import settings
from app.utils.logger import logger

# Настройки автоматических бэкапов из переменных окружения
BACKUP_ENABLED = settings.backup_enabled if hasattr(settings, 'backup_enabled') else True
BACKUP_TIME = settings.backup_time if hasattr(settings, 'backup_time') else '02:00'  # По умолчанию в 2:00 ночи
BACKUP_RETENTION_DAYS = settings.backup_retention_days if hasattr(settings, 'backup_retention_days') else 30  # Хранить 30 дней


async def run_scheduled_backup():
    """Запуск автоматического бэкапа"""
    if not BACKUP_ENABLED:
        logger.debug("Автоматические бэкапы отключены")
        return
    
    try:
        logger.info("Запуск автоматического бэкапа базы данных")
        backup_file = create_database_backup()
        logger.info(f"Автоматический бэкап успешно создан: {backup_file}")
        
        # Очистка старых бэкапов
        await cleanup_old_backups()
        
    except Exception as e:
        logger.error(f"Ошибка при создании автоматического бэкапа: {str(e)}", exc_info=True)


async def cleanup_old_backups():
    """Удаление старых бэкапов (старше BACKUP_RETENTION_DAYS дней)"""
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        
        backups = list_backups()
        deleted_count = 0
        
        for backup in backups:
            created_at = backup.get("created_at")
            if isinstance(created_at, datetime) and created_at < cutoff_date:
                try:
                    delete_backup(backup["path"])
                    deleted_count += 1
                    logger.info(f"Удален старый бэкап: {backup['filename']}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении старого бэкапа {backup['filename']}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Удалено старых бэкапов: {deleted_count}")
            
    except Exception as e:
        logger.error(f"Ошибка при очистке старых бэкапов: {str(e)}", exc_info=True)


async def scheduler_worker():
    """Фоновый worker для планировщика задач"""
    logger.info("Планировщик задач запущен")
    
    # Парсим время бэкапа
    hour, minute = map(int, BACKUP_TIME.split(':'))
    backup_time = time(hour, minute)
    last_backup_date = None
    
    while True:
        try:
            now = datetime.now()
            current_time = now.time()
            current_date = now.date()
            
            # Если текущее время совпадает с временем бэкапа и еще не делали бэкап сегодня
            if (current_time.hour == backup_time.hour and 
                current_time.minute == backup_time.minute and
                last_backup_date != current_date):
                
                await run_scheduled_backup()
                last_backup_date = current_date
                # Ждем минуту, чтобы не запускать дважды
                await asyncio.sleep(60)
            
            # Проверяем каждую минуту
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике задач: {str(e)}", exc_info=True)
            await asyncio.sleep(60)


def start_scheduler():
    """Запуск планировщика в фоновом режиме"""
    if not BACKUP_ENABLED:
        logger.info("Автоматические бэкапы отключены, планировщик не запущен")
        return None
    
    try:
        # Получаем или создаем event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Создаем фоновую задачу
        task = asyncio.create_task(scheduler_worker())
        logger.info(f"Планировщик автоматических бэкапов запущен. Время бэкапа: {BACKUP_TIME}, хранение: {BACKUP_RETENTION_DAYS} дней")
        return task
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {str(e)}", exc_info=True)
        return None


# Глобальная переменная для хранения задачи планировщика
_scheduler_task: Optional[asyncio.Task] = None

async def start_scheduler_async():
    """Асинхронный запуск планировщика (для использования в FastAPI startup)"""
    global _scheduler_task
    
    if not BACKUP_ENABLED:
        logger.info("Автоматические бэкапы отключены, планировщик не запущен")
        return None
    
    try:
        _scheduler_task = asyncio.create_task(scheduler_worker())
        logger.info(f"Планировщик автоматических бэкапов запущен. Время бэкапа: {BACKUP_TIME}, хранение: {BACKUP_RETENTION_DAYS} дней")
        return _scheduler_task
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {str(e)}", exc_info=True)
        return None
