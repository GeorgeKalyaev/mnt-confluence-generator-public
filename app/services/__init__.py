"""Сервисы приложения: бизнес-логика"""
from app.services.db_operations import (
    create_mnt, get_mnt, update_mnt, list_mnt,
    update_confluence_info, set_error_status,
    get_tags, create_tag, get_document_tags, set_document_tags,
    log_action, get_action_history,
    soft_delete_mnt, restore_mnt, get_mnt_with_deleted,
    create_document_version, get_latest_version_from_history, increment_version_number,
    get_document_versions, get_document_version,
    log_field_change, get_field_history, get_field_names_for_mnt
)
from app.services.confluence import get_confluence_client, ConfluenceClient, is_confluence_configured
from app.services.render import render_mnt_to_confluence_storage
from app.services.export import export_to_html, export_to_text
from app.services.backup import (
    create_database_backup, restore_database_backup, export_all_data,
    list_backups, delete_backup
)
from app.services.tag_templates import get_template_data_for_tags, get_available_templates, apply_template_to_data
from app.services.scheduler import start_scheduler_async

__all__ = [
    # DB operations
    'create_mnt', 'get_mnt', 'update_mnt', 'list_mnt',
    'update_confluence_info', 'set_error_status',
    'get_tags', 'create_tag', 'get_document_tags', 'set_document_tags',
    'log_action', 'get_action_history',
    'soft_delete_mnt', 'restore_mnt', 'get_mnt_with_deleted',
    'create_document_version', 'get_latest_version_from_history', 'increment_version_number',
    'get_document_versions', 'get_document_version',
    'log_field_change', 'get_field_history', 'get_field_names_for_mnt',
    # Confluence
    'get_confluence_client', 'ConfluenceClient', 'is_confluence_configured',
    # Render
    'render_mnt_to_confluence_storage',
    # Export
    'export_to_html', 'export_to_text',
    # Backup
    'create_database_backup', 'restore_database_backup', 'export_all_data',
    'list_backups', 'delete_backup',
    # Tag templates
    'get_template_data_for_tags', 'get_available_templates', 'apply_template_to_data',
    # Scheduler
    'start_scheduler_async',
]
