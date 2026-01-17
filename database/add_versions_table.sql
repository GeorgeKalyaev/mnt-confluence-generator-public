-- Таблица для хранения версий МНТ документов
CREATE TABLE IF NOT EXISTS mnt.document_versions (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL, -- Версия из таблицы "История изменений" (например, "0.1", "1.0")
    
    -- Основные поля документа
    title VARCHAR(500) NOT NULL,
    project VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    
    -- Все данные формы
    data_json JSONB NOT NULL DEFAULT '{}',
    
    -- Статус версии
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'error')),
    
    -- Информация о Confluence (если версия была опубликована)
    confluence_space VARCHAR(200),
    confluence_parent_id INTEGER,
    confluence_page_id INTEGER,
    confluence_page_url TEXT,
    last_publish_at TIMESTAMP,
    
    -- Метаданные версии
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(200) NOT NULL -- Автор, который создал эту версию
    
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_document_versions_mnt_id ON mnt.document_versions(mnt_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_version_number ON mnt.document_versions(mnt_id, version_number);
CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON mnt.document_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_document_versions_status ON mnt.document_versions(status);

-- Комментарии
COMMENT ON TABLE mnt.document_versions IS 'Таблица для хранения версий МНТ документов';
COMMENT ON COLUMN mnt.document_versions.version_number IS 'Номер версии из таблицы "История изменений" (например, "0.1", "1.0")';
COMMENT ON COLUMN mnt.document_versions.data_json IS 'Полные данные МНТ на момент создания версии';
COMMENT ON COLUMN mnt.document_versions.created_by IS 'Автор, который создал эту версию (берется из поля "Автор" формы)';
