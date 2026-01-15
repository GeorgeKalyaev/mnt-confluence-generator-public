# МНТ Confluence Generator

Сервис для автоматической генерации МНТ (Методика Нагрузочного Тестирования) в Confluence из веб-формы.

## Технологии

- **Backend**: FastAPI (Python 3.10+)
- **База данных**: PostgreSQL
- **UI**: HTML + Bootstrap 5 + Jinja2
- **Интеграция**: Confluence REST API

## Установка и запуск

**📖 Подробная инструкция:** См. файл [INSTALL.md](INSTALL.md)

**⚡ Быстрый старт:** См. файл [QUICKSTART.md](QUICKSTART.md)

### Краткая инструкция:

1. **Установите Python 3.10+** (если не установлен): https://www.python.org/downloads/
   - При установке отметьте "Add Python to PATH"

2. **Установите PostgreSQL** (если не установлен): https://www.postgresql.org/download/windows/

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Создайте базу данных:**
   - Откройте pgAdmin
   - Создайте базу данных `mnt_db`
   - Выполните SQL скрипт из `database/schema.sql`

5. **Создайте файл `.env`** в корне проекта:
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

6. **Запустите приложение:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

7. **Откройте в браузере:** http://localhost:8000

## Структура проекта

```
mnt-confluence-generator/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── models.py            # Модели данных
│   ├── database.py          # Подключение к БД
│   ├── confluence.py        # Интеграция с Confluence API
│   ├── render.py            # Генерация контента для Confluence
│   └── templates/           # HTML шаблоны (Jinja2)
│       ├── base.html
│       ├── create.html
│       ├── list.html
│       └── edit.html
├── database/
│   └── schema.sql           # SQL схема БД
├── .env.example             # Пример конфигурации
├── requirements.txt         # Зависимости Python
└── README.md               # Этот файл
```

## Использование

1. Откройте http://localhost:8000/mnt/create
2. Заполните форму с данными МНТ
3. Укажите Space Key и (опционально) Parent Page ID в Confluence
4. Нажмите "Сохранить и сгенерировать в Confluence"
5. Получите ссылку на созданную страницу в списке МНТ

## Важные замечания

- Перед первым запуском убедитесь, что PostgreSQL запущен и база данных создана
- Настройте файл `.env` с параметрами подключения к БД и Confluence
- Для Confluence Cloud используйте `CONFLUENCE_EMAIL` и `CONFLUENCE_API_TOKEN`
- Для Confluence Server/Datacenter используйте `CONFLUENCE_USERNAME` и `CONFLUENCE_PASSWORD`
- Space Key можно найти в URL Confluence (например, если URL `.../spaces/TEST/...`, то Space Key = `TEST`)
- Parent Page ID можно найти в URL страницы Confluence (параметр `pageId`)

## API Endpoints

- `GET /` - редирект на список МНТ
- `GET /mnt/list` - список всех МНТ
- `GET /mnt/create` - форма создания МНТ
- `GET /mnt/{id}/edit` - форма редактирования МНТ
- `GET /mnt/{id}/view` - просмотр МНТ в JSON формате
- `POST /api/mnt` - API: создание МНТ
- `GET /api/mnt` - API: список МНТ
- `GET /api/mnt/{id}` - API: получение МНТ
- `PUT /api/mnt/{id}` - API: обновление МНТ
- `POST /api/mnt/{id}/publish` - API: публикация/обновление в Confluence
