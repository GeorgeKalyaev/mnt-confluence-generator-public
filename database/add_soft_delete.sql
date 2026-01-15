-- Миграция: Добавление soft delete (мягкого удаления) для МНТ

-- Добавляем поле deleted_at для пометки удаленных записей
ALTER TABLE mnt.documents 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;

-- Создаем индекс для быстрого поиска удаленных записей
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON mnt.documents(deleted_at);

-- Комментарий к полю
COMMENT ON COLUMN mnt.documents.deleted_at IS 'Дата мягкого удаления (NULL = не удален, TIMESTAMP = дата удаления)';
