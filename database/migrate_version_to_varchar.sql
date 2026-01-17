-- Миграция: изменение типа version_number с INTEGER на VARCHAR
-- Это позволяет хранить версии в формате "0.1", "0.2" и т.д. из history_changes_table

-- Шаг 1: Создаем временную колонку
ALTER TABLE mnt.document_versions 
ADD COLUMN IF NOT EXISTS version_number_new VARCHAR(20);

-- Шаг 2: Преобразуем существующие INTEGER версии в строки (1 -> "1", 2 -> "2" и т.д.)
UPDATE mnt.document_versions 
SET version_number_new = version_number::TEXT;

-- Шаг 3: Удаляем старую колонку и constraint
ALTER TABLE mnt.document_versions 
DROP CONSTRAINT IF EXISTS unique_document_version;

ALTER TABLE mnt.document_versions 
DROP COLUMN IF EXISTS version_number;

-- Шаг 4: Переименовываем новую колонку
ALTER TABLE mnt.document_versions 
RENAME COLUMN version_number_new TO version_number;

-- Шаг 5: Восстанавливаем constraint
ALTER TABLE mnt.document_versions 
ADD CONSTRAINT unique_document_version UNIQUE(document_id, version_number);

-- Шаг 6: Устанавливаем NOT NULL
ALTER TABLE mnt.document_versions 
ALTER COLUMN version_number SET NOT NULL;
