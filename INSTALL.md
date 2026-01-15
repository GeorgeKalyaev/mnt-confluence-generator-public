# Инструкция по установке и запуску

## Шаг 1: Установка Python

Если Python не установлен, нужно его установить:

1. Скачайте Python 3.10 или новее с официального сайта: https://www.python.org/downloads/
2. При установке **обязательно отметьте галочку "Add Python to PATH"**
3. После установки проверьте в командной строке (cmd или PowerShell):
   ```
   python --version
   ```
   Должно показать что-то вроде: `Python 3.10.x`

## Шаг 2: Установка зависимостей

Откройте командную строку (cmd) или PowerShell в папке проекта:

```bash
cd C:\Users\kalya\mnt-confluence-generator
pip install -r requirements.txt
```

Если `pip` не найден, попробуйте:
```bash
python -m pip install -r requirements.txt
```

## Шаг 3: Настройка базы данных PostgreSQL

### 3.1. Установка PostgreSQL (если не установлена)

1. Скачайте PostgreSQL: https://www.postgresql.org/download/windows/
2. Установите, запомните пароль для пользователя `postgres`
3. PostgreSQL обычно запускается автоматически как служба Windows

### 3.2. Создание базы данных

Откройте **pgAdmin** (интерфейс PostgreSQL) или используйте командную строку:

1. Откройте pgAdmin
2. Подключитесь к серверу PostgreSQL
3. Создайте новую базу данных (правый клик на "Databases" -> "Create" -> "Database")
   - Имя: `mnt_db` (или любое другое)
4. Выполните SQL скрипт: откройте файл `database/schema.sql` и выполните его в Query Tool

ИЛИ через командную строку:
```bash
psql -U postgres
CREATE DATABASE mnt_db;
\q
psql -U postgres -d mnt_db -f database/schema.sql
```

## Шаг 4: Создание файла .env

Создайте файл `.env` в папке проекта (`mnt-confluence-generator`) со следующим содержимым:

```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mnt_db
DATABASE_USER=postgres
DATABASE_PASSWORD=ваш_пароль_postgres

# Confluence Configuration (пока можно оставить значения по умолчанию)
CONFLUENCE_URL=https://your-confluence.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

**Важно:** Замените `ваш_пароль_postgres` на пароль, который вы задали при установке PostgreSQL.

## Шаг 5: Запуск приложения

В командной строке (cmd или PowerShell) в папке проекта выполните:

```bash
cd C:\Users\kalya\mnt-confluence-generator
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Если команда не работает, попробуйте:
```bash
python -m uvicorn app.main:app --reload
```

После запуска вы увидите сообщение типа:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Шаг 6: Открытие в браузере

Откройте браузер и перейдите по адресу:
- http://localhost:8000
- или http://127.0.0.1:8000

## Возможные проблемы

### Проблема: "python не является внутренней или внешней командой"
**Решение:** Python не добавлен в PATH. Переустановите Python с галочкой "Add Python to PATH" или добавьте Python вручную в переменные окружения.

### Проблема: "ModuleNotFoundError: No module named 'fastapi'"
**Решение:** Установите зависимости: `pip install -r requirements.txt`

### Проблема: "could not connect to server"
**Решение:** Убедитесь, что PostgreSQL запущен. Проверьте службу PostgreSQL в "Службы" Windows.

### Проблема: "password authentication failed"
**Решение:** Проверьте пароль в файле `.env` - он должен совпадать с паролем пользователя postgres.

## Упрощенный вариант (без PostgreSQL - для тестирования)

Если нужно просто посмотреть как работает интерфейс, можно временно использовать SQLite (но это потребует изменения кода). 
Для полной функциональности нужна PostgreSQL.
