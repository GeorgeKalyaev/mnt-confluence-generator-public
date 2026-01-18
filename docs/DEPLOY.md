# Развертывание для DevOps

Инструкция для быстрого развертывания проекта в корпоративной среде.

## 🐳 Docker Compose (Рекомендуемый способ)

Самый быстрый способ развернуть весь проект одной командой.

### Требования

- Docker 20.10+
- Docker Compose 2.0+

### Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd mnt-confluence-generator
   ```

2. **Создайте файл `.env` с настройками:**
   ```env
   # База данных (используются значения из docker-compose по умолчанию)
   DATABASE_HOST=postgres
   DATABASE_PORT=5432
   DATABASE_NAME=mnt_db
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   
   # Confluence
   CONFLUENCE_URL=https://your-company.atlassian.net
   CONFLUENCE_EMAIL=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token
   
   # Или для Confluence Server:
   # CONFLUENCE_URL=http://confluence.company.local:8090
   # CONFLUENCE_USERNAME=admin
   # CONFLUENCE_PASSWORD=admin
   
   # Логирование
   LOG_LEVEL=INFO
   LOG_FORMAT=text
   LOG_ENVIRONMENT=production
   ```

3. **Запустите все сервисы:**
   ```bash
   docker-compose -f docker-compose.full.yml up -d
   ```

4. **Проверьте статус:**
   ```bash
   docker-compose -f docker-compose.full.yml ps
   ```

5. **Откройте приложение:**
   - Приложение: http://localhost:8000
   - База данных будет автоматически инициализирована скриптом `database/schema.sql`

### Опционально: Запуск с локальным Confluence для тестирования

```bash
docker-compose -f docker-compose.full.yml --profile confluence up -d
```

Confluence будет доступен на http://localhost:8090

### Остановка

```bash
docker-compose -f docker-compose.full.yml down
```

### Остановка с удалением данных

```bash
docker-compose -f docker-compose.full.yml down -v
```

## 🔧 Ручная установка (без Docker)

Для развертывания на сервере без Docker.

### Требования

- Python 3.10+
- PostgreSQL 12+
- pip

### Шаги установки

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Настройте PostgreSQL:**
   ```bash
   # Создайте базу данных
   psql -U postgres -c "CREATE DATABASE mnt_db;"
   
   # Выполните схему
   psql -U postgres -d mnt_db -f database/schema.sql
   ```

3. **Настройте `.env` файл** (см. пример выше)

4. **Запустите приложение:**
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

   Или через systemd (для production):
   
   Создайте файл `/etc/systemd/system/mnt-generator.service`:
   ```ini
   [Unit]
   Description=MNT Confluence Generator
   After=network.target postgresql.service
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/mnt-confluence-generator
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Запустите:
   ```bash
   sudo systemctl enable mnt-generator
   sudo systemctl start mnt-generator
   ```

## 🔒 Безопасность для Production

1. **Измените пароли БД** в `.env` и `docker-compose.full.yml`
2. **Используйте HTTPS** через reverse proxy (nginx/Apache)
3. **Ограничьте доступ** к портам 8000 и 5432 только внутри сети
4. **Настройте бэкапы** базы данных PostgreSQL
5. **Используйте секреты** вместо `.env` файлов (Kubernetes Secrets, Docker Secrets, etc.)

## 📊 Мониторинг

- Логи приложения: `logs/app_*.log`
- Логи Docker: `docker-compose -f docker-compose.full.yml logs -f app`
- Проверка здоровья: `curl http://localhost:8000/`

## 🔄 Обновление

1. Остановите приложение
2. Обновите код: `git pull`
3. Пересоберите образ: `docker-compose -f docker-compose.full.yml build`
4. Запустите: `docker-compose -f docker-compose.full.yml up -d`

## 📝 Примечания

- База данных автоматически инициализируется при первом запуске через `docker-entrypoint-initdb.d`
- Все данные PostgreSQL хранятся в Docker volume `postgres-data`
- Логи сохраняются в папке `logs/` на хосте
