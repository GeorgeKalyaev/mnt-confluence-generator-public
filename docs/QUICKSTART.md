# Быстрый старт

Для опытных пользователей, которые уже знакомы с Python и PostgreSQL.

## Предварительные требования

- ✅ Python 3.10+ установлен
- ✅ PostgreSQL 12+ установлен и запущен
- ✅ Git установлен (для клонирования репозитория)

## Шаги установки

### 1. Клонирование и установка зависимостей

```bash
# Клонировать репозиторий
git clone <repository-url>
cd mnt-confluence-generator

# Установить зависимости
pip install -r requirements.txt
```

### 2. Создание и настройка базы данных

```bash
# Создать базу данных
psql -U postgres -c "CREATE DATABASE mnt_db;"

# Импортировать схему
psql -U postgres -d mnt_db -f database/schema.sql
```

**Важно:** Обязательно выполните `database/schema.sql` - без него приложение не будет работать!

### 3. Создание файла .env

Создайте файл `.env` в корне проекта:

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mnt_db
DATABASE_USER=postgres
DATABASE_PASSWORD=ваш_пароль

# Confluence (опционально)
CONFLUENCE_URL=https://your-company.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# Или для Server:
# CONFLUENCE_URL=http://localhost:8090
# CONFLUENCE_USERNAME=admin
# CONFLUENCE_PASSWORD=admin

# Logging (опционально)
LOG_LEVEL=INFO
LOG_FORMAT=text
```

### 4. Запуск приложения

```bash
python -m uvicorn app.main:app --reload
```

### 5. Открыть в браузере

http://localhost:8000

## Что создается при выполнении schema.sql

- ✅ Схема `mnt`
- ✅ Таблица `mnt.documents` (документы МНТ)
- ✅ Таблица `mnt.action_history` (история действий)
- ✅ Все необходимые индексы для производительности
- ✅ Триггеры для автоматического обновления временных меток

## Проверка установки

1. Приложение запускается без ошибок
2. Открывается http://localhost:8000
3. Можно создать новый МНТ через веб-интерфейс

## Проблемы?

См. подробную инструкцию в [INSTALL.md](INSTALL.md) или раздел "Решение проблем" в [README.md](README.md).

---

**Для подробной установки см. [INSTALL.md](INSTALL.md)**
