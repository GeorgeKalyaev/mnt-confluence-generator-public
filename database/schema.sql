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

-- Индекс для мягкого удаления
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON mnt.documents(deleted_at);

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

-- Комментарии к таблице и полям
COMMENT ON SCHEMA mnt IS 'Схема для хранения данных МНТ (Методика Нагрузочного Тестирования)';
COMMENT ON TABLE mnt.documents IS 'Таблица документов МНТ';
COMMENT ON COLUMN mnt.documents.data_json IS 'Все поля формы хранятся в JSON формате';
COMMENT ON COLUMN mnt.documents.status IS 'Статус: draft - черновик, published - опубликовано, error - ошибка публикации';
