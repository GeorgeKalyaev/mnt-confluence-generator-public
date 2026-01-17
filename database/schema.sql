-- Создание схемы mnt
CREATE SCHEMA IF NOT EXISTS mnt;

-- Таблица для хранения документов МНТ
CREATE TABLE IF NOT EXISTS mnt.documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    project VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'error')),
    
    -- Все данные формы хранятся в JSON
    data_json JSONB NOT NULL DEFAULT '{}',
    
    -- Информация о Confluence
    confluence_space VARCHAR(200),
    confluence_parent_id INTEGER,
    confluence_page_id INTEGER,
    confluence_page_url TEXT,
    last_publish_at TIMESTAMP,
    last_error TEXT,
    
    -- Мягкое удаление (soft delete)
    deleted_at TIMESTAMP NULL
);

-- Индекс для быстрого поиска по статусу
CREATE INDEX IF NOT EXISTS idx_documents_status ON mnt.documents(status);

-- Индекс для поиска по проекту
CREATE INDEX IF NOT EXISTS idx_documents_project ON mnt.documents(project);

-- Индекс для поиска по автору
CREATE INDEX IF NOT EXISTS idx_documents_author ON mnt.documents(author);

-- Индекс для поиска по Confluence page_id
CREATE INDEX IF NOT EXISTS idx_documents_confluence_page_id ON mnt.documents(confluence_page_id);

-- Индекс для фильтрации по deleted_at (soft delete) - частичный индекс для не удаленных
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON mnt.documents(deleted_at) WHERE deleted_at IS NULL;

-- Индексы для сортировки (часто используются в ORDER BY)
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON mnt.documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON mnt.documents(updated_at DESC);

-- GIN индекс для быстрого поиска по JSONB содержимому (теги, поиск по содержимому)
CREATE INDEX IF NOT EXISTS idx_documents_data_json_gin ON mnt.documents USING GIN (data_json);

-- Составной индекс для частых запросов: фильтр по статусу и deleted_at с сортировкой по created_at
CREATE INDEX IF NOT EXISTS idx_documents_status_deleted_created ON mnt.documents(status, deleted_at, created_at DESC) WHERE deleted_at IS NULL;

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION mnt.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON mnt.documents
    FOR EACH ROW
    EXECUTE FUNCTION mnt.update_updated_at_column();

-- Таблица для истории действий пользователей
CREATE TABLE IF NOT EXISTS mnt.action_history (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    user_name VARCHAR(200) NOT NULL,
    action_type VARCHAR(100) NOT NULL, -- 'created', 'updated', 'published', 'deleted', 'status_changed', etc.
    action_description TEXT,
    details JSONB, -- Дополнительные детали действия в JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска по истории действий
CREATE INDEX IF NOT EXISTS idx_action_history_mnt_id ON mnt.action_history(mnt_id);
CREATE INDEX IF NOT EXISTS idx_action_history_created_at ON mnt.action_history(created_at);
CREATE INDEX IF NOT EXISTS idx_action_history_action_type ON mnt.action_history(action_type);

-- Комментарии к схеме, таблицам и полям
COMMENT ON SCHEMA mnt IS 'Схема для хранения данных МНТ (Методика Нагрузочного Тестирования)';
COMMENT ON TABLE mnt.documents IS 'Таблица документов МНТ';
COMMENT ON COLUMN mnt.documents.data_json IS 'Все поля формы хранятся в JSON формате';
COMMENT ON COLUMN mnt.documents.status IS 'Статус: draft - черновик, published - опубликовано, error - ошибка публикации';
COMMENT ON COLUMN mnt.documents.deleted_at IS 'Метка мягкого удаления. NULL - документ не удален, TIMESTAMP - дата удаления';
COMMENT ON TABLE mnt.action_history IS 'История действий пользователей с МНТ документами';
COMMENT ON COLUMN mnt.action_history.action_type IS 'Тип действия: created, updated, published, deleted, status_changed, etc.';
COMMENT ON COLUMN mnt.action_history.details IS 'Дополнительные детали действия в формате JSON';
