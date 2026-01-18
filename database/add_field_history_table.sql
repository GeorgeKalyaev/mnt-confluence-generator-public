-- Создание таблицы для истории изменений полей МНТ
CREATE TABLE IF NOT EXISTS mnt.field_history (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    
    -- Какое поле было изменено
    field_name VARCHAR(200) NOT NULL,  -- Например: "title", "project", "author", "data_json.introduction_text", etc.
    field_path TEXT NOT NULL,  -- Путь к полю в JSON, например: "title", "data_json.introduction_text"
    
    -- Значения
    old_value TEXT,  -- Старое значение (может быть JSON для сложных полей)
    new_value TEXT,  -- Новое значение (может быть JSON для сложных полей)
    
    -- Метаданные изменения
    changed_by VARCHAR(200) NOT NULL,  -- Кто изменил (автор)
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Когда изменил
    
    -- Дополнительная информация
    change_type VARCHAR(50) DEFAULT 'update' CHECK (change_type IN ('create', 'update', 'delete')),
    description TEXT,  -- Описание изменения (опционально)
    
    -- Связь с версией документа (если есть)
    document_version_id INTEGER REFERENCES mnt.document_versions(id) ON DELETE SET NULL
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_field_history_mnt_id ON mnt.field_history(mnt_id);
CREATE INDEX IF NOT EXISTS idx_field_history_field_name ON mnt.field_history(mnt_id, field_name);
CREATE INDEX IF NOT EXISTS idx_field_history_changed_at ON mnt.field_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_field_history_changed_by ON mnt.field_history(changed_by);

-- Комментарии
COMMENT ON TABLE mnt.field_history IS 'История изменений конкретных полей МНТ документов';
COMMENT ON COLUMN mnt.field_history.field_name IS 'Название поля (например: title, project, author, introduction_text)';
COMMENT ON COLUMN mnt.field_history.field_path IS 'Путь к полю в структуре данных (например: title, data_json.introduction_text)';
COMMENT ON COLUMN mnt.field_history.old_value IS 'Старое значение поля (может быть JSON)';
COMMENT ON COLUMN mnt.field_history.new_value IS 'Новое значение поля (может быть JSON)';
COMMENT ON COLUMN mnt.field_history.changed_by IS 'Автор изменения (берется из поля author формы)';
