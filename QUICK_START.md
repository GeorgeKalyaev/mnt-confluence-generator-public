# 🚀 Быстрый запуск приложения

## Вариант 1: Docker Compose (самый простой)

### Шаг 1: Установите Docker Desktop
Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Шаг 2: Создайте файл `.env`
В корне проекта создайте файл `.env` со следующим содержимым:

```env
# База данных (для Docker Compose можно оставить как есть)
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=mnt_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Confluence (заполните, если нужно публиковать в Confluence)
# Для Confluence Cloud:
CONFLUENCE_URL=https://your-company.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# ИЛИ для Confluence Server:
# CONFLUENCE_URL=http://localhost:8090
# CONFLUENCE_USERNAME=admin
# CONFLUENCE_PASSWORD=admin

# Логирование (можно оставить по умолчанию)
LOG_LEVEL=INFO
LOG_FORMAT=text
LOG_ENVIRONMENT=development
```

### Шаг 3: Запустите приложение
Откройте PowerShell или командную строку в папке проекта и выполните:

```bash
docker-compose -f docker-compose.full.yml up -d
```

### Шаг 4: Откройте в браузере
Приложение будет доступно по адресу: **http://localhost:8000**

### Остановка приложения
```bash
docker-compose -f docker-compose.full.yml down
```

---

## Вариант 2: Ручная установка (без Docker)

### Шаг 1: Установите Python 3.10+
Скачайте с [python.org](https://www.python.org/downloads/)

### Шаг 2: Установите PostgreSQL 12+
Скачайте с [postgresql.org](https://www.postgresql.org/download/)

### Шаг 3: Установите зависимости Python
```bash
pip install -r requirements.txt
```

### Шаг 4: Создайте базу данных
Откройте **pgAdmin** или используйте командную строку:

**Через pgAdmin:**
1. Откройте pgAdmin
2. Подключитесь к серверу PostgreSQL
3. Правый клик на "Databases" → "Create" → "Database"
4. Имя: `mnt_db`
5. Нажмите "Save"

**Через командную строку:**
```bash
psql -U postgres
CREATE DATABASE mnt_db;
\q
```

### Шаг 5: Импортируйте схему базы данных
**Через pgAdmin:**
1. Выберите базу данных `mnt_db`
2. Откройте "Query Tool" (правый клик → "Query Tool")
3. Откройте файл `database/schema.sql`
4. Скопируйте весь код
5. Вставьте в Query Tool
6. Нажмите "Execute" (F5)

**Через командную строку:**
```bash
psql -U postgres -d mnt_db -f database/schema.sql
```

### Шаг 6: Создайте файл `.env`
В корне проекта создайте файл `.env`:

```env
# База данных
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mnt_db
DATABASE_USER=postgres
DATABASE_PASSWORD=ваш_пароль_postgres

# Confluence (заполните, если нужно)
CONFLUENCE_URL=https://your-company.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=text
LOG_ENVIRONMENT=development
```

### Шаг 7: Запустите приложение
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Шаг 8: Откройте в браузере
Приложение будет доступно по адресу: **http://localhost:8000**

---

## ✅ Проверка работы

После запуска вы должны увидеть:
- В консоли: `INFO:     Uvicorn running on http://0.0.0.0:8000`
- В браузере: Главную страницу со списком МНТ документов

## 🔧 Решение проблем

### Ошибка подключения к базе данных
- Проверьте, что PostgreSQL запущен
- Проверьте правильность данных в `.env` файле
- Убедитесь, что база данных `mnt_db` создана

### Порт 8000 занят
Измените порт в команде запуска:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Ошибки при установке зависимостей
Обновите pip:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
