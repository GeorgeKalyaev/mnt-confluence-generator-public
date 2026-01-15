-- Таблица для истории изменений МНТ
CREATE TABLE IF NOT EXISTS mnt.document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    data_json JSONB NOT NULL,
    changed_by VARCHAR(200),
    change_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_document_version UNIQUE(document_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON mnt.document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON mnt.document_versions(created_at);

-- Таблица для тегов МНТ
CREATE TABLE IF NOT EXISTS mnt.tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#6c757d',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mnt.document_tags (
    document_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES mnt.tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON mnt.document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON mnt.document_tags(tag_id);

COMMENT ON TABLE mnt.document_versions IS 'История версий документов МНТ';
COMMENT ON TABLE mnt.tags IS 'Теги для категоризации МНТ';
COMMENT ON TABLE mnt.document_tags IS 'Связь документов и тегов (многие ко многим)';
