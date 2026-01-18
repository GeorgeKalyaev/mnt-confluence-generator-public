"""Утилиты приложения: вспомогательные функции"""
from app.utils.logger import (
    log_mnt_operation, log_error, log_confluence_operation,
    log_user_action, log_request, logger, generate_request_id, log_security_event
)
from app.utils.validation import sanitize_dict, validate_mnt_data, sanitize_search_query
from app.utils.exceptions import (
    AppException, NotFoundError, AppValidationError, DatabaseError, ConfluenceError, SecurityError,
    app_exception_handler, validation_exception_handler, database_exception_handler, general_exception_handler
)
from app.utils.defaults import get_default_mnt_data
from app.utils.completeness_checker import check_document_completeness
from app.utils.diff_tracker import compare_mnt_data
from app.utils.version_diff import compare_versions

__all__ = [
    # Logger
    'log_mnt_operation', 'log_error', 'log_confluence_operation',
    'log_user_action', 'log_request', 'logger', 'generate_request_id', 'log_security_event',
    # Validation
    'sanitize_dict', 'validate_mnt_data', 'sanitize_search_query',
    # Exceptions
    'AppException', 'NotFoundError', 'AppValidationError', 'DatabaseError', 'ConfluenceError', 'SecurityError',
    'app_exception_handler', 'validation_exception_handler', 'database_exception_handler', 'general_exception_handler',
    # Defaults
    'get_default_mnt_data',
    # Completeness
    'check_document_completeness',
    # Diff tracking
    'compare_mnt_data', 'compare_versions',
]
