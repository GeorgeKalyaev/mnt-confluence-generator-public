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

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_action_history_mnt_id ON mnt.action_history(mnt_id);
CREATE INDEX IF NOT EXISTS idx_action_history_created_at ON mnt.action_history(created_at);
CREATE INDEX IF NOT EXISTS idx_action_history_action_type ON mnt.action_history(action_type);

-- Комментарии
COMMENT ON TABLE mnt.action_history IS 'История действий пользователей с МНТ документами';
COMMENT ON COLUMN mnt.action_history.action_type IS 'Тип действия: created, updated, published, deleted, status_changed, etc.';
COMMENT ON COLUMN mnt.action_history.details IS 'Дополнительные детали действия в формате JSON';
