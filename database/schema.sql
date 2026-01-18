-- РЎРѕР·РґР°РЅРёРµ СЃС…РµРјС‹ mnt
CREATE SCHEMA IF NOT EXISTS mnt;

-- РўР°Р±Р»РёС†Р° РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚РѕРІ РњРќРў
CREATE TABLE IF NOT EXISTS mnt.documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    project VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'error')),
    
    -- Р’СЃРµ РґР°РЅРЅС‹Рµ С„РѕСЂРјС‹ С…СЂР°РЅСЏС‚СЃСЏ РІ JSON
    data_json JSONB NOT NULL DEFAULT '{}',
    
    -- РРЅС„РѕСЂРјР°С†РёСЏ Рѕ Confluence
    confluence_space VARCHAR(200),
    confluence_parent_id INTEGER,
    confluence_page_id INTEGER,
    confluence_page_url TEXT,
    last_publish_at TIMESTAMP,
    last_error TEXT,
    deleted_at TIMESTAMP NULL
);

-- РРЅРґРµРєСЃ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїРѕРёСЃРєР° РїРѕ СЃС‚Р°С‚СѓСЃСѓ
CREATE INDEX IF NOT EXISTS idx_documents_status ON mnt.documents(status);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РїРѕ РїСЂРѕРµРєС‚Сѓ
CREATE INDEX IF NOT EXISTS idx_documents_project ON mnt.documents(project);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РїРѕ Р°РІС‚РѕСЂСѓ
CREATE INDEX IF NOT EXISTS idx_documents_author ON mnt.documents(author);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РїРѕ Confluence page_id
CREATE INDEX IF NOT EXISTS idx_documents_confluence_page_id ON mnt.documents(confluence_page_id);
CREATE INDEX IF NOT EXISTS idx_documents_deleted_at ON mnt.documents(deleted_at);

-- Р¤СѓРЅРєС†РёСЏ РґР»СЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ updated_at
CREATE OR REPLACE FUNCTION mnt.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- РўСЂРёРіРіРµСЂ РґР»СЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON mnt.documents
    FOR EACH ROW
    EXECUTE FUNCTION mnt.update_updated_at_column();

-- РўР°Р±Р»РёС†Р° РґР»СЏ РёСЃС‚РѕСЂРёРё РґРµР№СЃС‚РІРёР№ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№
CREATE TABLE IF NOT EXISTS mnt.action_history (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    user_name VARCHAR(200) NOT NULL,
    action_type VARCHAR(100) NOT NULL, -- 'created', 'updated', 'published', 'deleted', 'status_changed', etc.
    action_description TEXT,
    details JSONB, -- Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РґРµС‚Р°Р»Рё РґРµР№СЃС‚РІРёСЏ РІ JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- РРЅРґРµРєСЃС‹ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїРѕРёСЃРєР°
CREATE INDEX IF NOT EXISTS idx_action_history_mnt_id ON mnt.action_history(mnt_id);
CREATE INDEX IF NOT EXISTS idx_action_history_created_at ON mnt.action_history(created_at);
CREATE INDEX IF NOT EXISTS idx_action_history_action_type ON mnt.action_history(action_type);

-- РљРѕРјРјРµРЅС‚Р°СЂРёРё Рє С‚Р°Р±Р»РёС†Рµ Рё РїРѕР»СЏРј
COMMENT ON SCHEMA mnt IS 'РЎС…РµРјР° РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РґР°РЅРЅС‹С… РњРќРў (РњРµС‚РѕРґРёРєР° РќР°РіСЂСѓР·РѕС‡РЅРѕРіРѕ РўРµСЃС‚РёСЂРѕРІР°РЅРёСЏ)';
COMMENT ON TABLE mnt.documents IS 'РўР°Р±Р»РёС†Р° РґРѕРєСѓРјРµРЅС‚РѕРІ РњРќРў';
COMMENT ON COLUMN mnt.documents.data_json IS 'Р’СЃРµ РїРѕР»СЏ С„РѕСЂРјС‹ С…СЂР°РЅСЏС‚СЃСЏ РІ JSON С„РѕСЂРјР°С‚Рµ';
COMMENT ON COLUMN mnt.documents.status IS 'РЎС‚Р°С‚СѓСЃ: draft - С‡РµСЂРЅРѕРІРёРє, published - РѕРїСѓР±Р»РёРєРѕРІР°РЅРѕ, error - РѕС€РёР±РєР° РїСѓР±Р»РёРєР°С†РёРё';
COMMENT ON TABLE mnt.action_history IS 'РСЃС‚РѕСЂРёСЏ РґРµР№СЃС‚РІРёР№ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ СЃ РњРќРў РґРѕРєСѓРјРµРЅС‚Р°РјРё';
COMMENT ON COLUMN mnt.action_history.action_type IS 'РўРёРї РґРµР№СЃС‚РІРёСЏ: created, updated, published, deleted, status_changed, etc.';
COMMENT ON COLUMN mnt.action_history.details IS 'Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ РґРµС‚Р°Р»Рё РґРµР№СЃС‚РІРёСЏ РІ С„РѕСЂРјР°С‚Рµ JSON';

-- РўР°Р±Р»РёС†Р° РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РІРµСЂСЃРёР№ РњРќРў РґРѕРєСѓРјРµРЅС‚РѕРІ
CREATE TABLE IF NOT EXISTS mnt.document_versions (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    version_number VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    project VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    data_json JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'error')),
    confluence_space VARCHAR(200),
    confluence_parent_id INTEGER,
    confluence_page_id INTEGER,
    confluence_page_url TEXT,
    last_publish_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(200) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_document_versions_mnt_id ON mnt.document_versions(mnt_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_version_number ON mnt.document_versions(mnt_id, version_number);
CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON mnt.document_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_document_versions_status ON mnt.document_versions(status);

-- РўР°Р±Р»РёС†Р° РґР»СЏ РёСЃС‚РѕСЂРёРё РёР·РјРµРЅРµРЅРёР№ РїРѕР»РµР№ РњРќРў
CREATE TABLE IF NOT EXISTS mnt.field_history (
    id SERIAL PRIMARY KEY,
    mnt_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    field_name VARCHAR(200) NOT NULL,
    field_path TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(200) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_type VARCHAR(50) DEFAULT 'update' CHECK (change_type IN ('create', 'update', 'delete')),
    description TEXT,
    document_version_id INTEGER REFERENCES mnt.document_versions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_field_history_mnt_id ON mnt.field_history(mnt_id);
CREATE INDEX IF NOT EXISTS idx_field_history_field_name ON mnt.field_history(mnt_id, field_name);
CREATE INDEX IF NOT EXISTS idx_field_history_changed_at ON mnt.field_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_field_history_changed_by ON mnt.field_history(changed_by);

-- РўР°Р±Р»РёС†С‹ РґР»СЏ С‚РµРіРѕРІ
CREATE TABLE IF NOT EXISTS mnt.tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mnt.document_tags (
    document_id INTEGER NOT NULL REFERENCES mnt.documents(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES mnt.tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_document_tags_document_id ON mnt.document_tags(document_id);
CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON mnt.document_tags(tag_id);

-- GIN РёРЅРґРµРєСЃС‹ РґР»СЏ JSONB РїРѕР»РµР№
CREATE INDEX IF NOT EXISTS idx_documents_data_json_gin ON mnt.documents USING GIN (data_json);
CREATE INDEX IF NOT EXISTS idx_document_versions_data_json_gin ON mnt.document_versions USING GIN (data_json);

COMMENT ON TABLE mnt.document_versions IS 'РўР°Р±Р»РёС†Р° РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РІРµСЂСЃРёР№ РњРќРў РґРѕРєСѓРјРµРЅС‚РѕРІ';
COMMENT ON TABLE mnt.field_history IS 'РСЃС‚РѕСЂРёСЏ РёР·РјРµРЅРµРЅРёР№ РєРѕРЅРєСЂРµС‚РЅС‹С… РїРѕР»РµР№ РњРќРў РґРѕРєСѓРјРµРЅС‚РѕРІ';
