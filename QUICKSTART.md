# Быстрый старт

## Минимальные требования для запуска:

1. **Python 3.10+** - https://www.python.org/downloads/
2. **PostgreSQL** - https://www.postgresql.org/download/windows/
3. **Файл .env** с настройками

## Команды для запуска (после установки Python и PostgreSQL):

```bash
# 1. Перейти в папку проекта
cd C:\Users\kalya\mnt-confluence-generator

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать базу данных (в pgAdmin или через psql)
# Выполнить файл database/schema.sql

# 4. Создать файл .env (см. пример ниже)

# 5. Запустить сервер
python -m uvicorn app.main:app --reload

# 6. Открыть в браузере: http://localhost:8000
```

## Пример файла .env:

Создайте файл `.env` в корне проекта:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=mnt_db
DATABASE_USER=postgres
DATABASE_PASSWORD=ваш_пароль

CONFLUENCE_URL=https://your-confluence.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

## Проверка что все работает:

1. Python установлен: `python --version`
2. Зависимости установлены: `pip list | findstr fastapi`
3. PostgreSQL запущен: проверьте в "Службы" Windows
4. Сервер запускается без ошибок
5. Браузер открывает http://localhost:8000
