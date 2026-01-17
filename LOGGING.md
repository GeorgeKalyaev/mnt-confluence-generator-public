# Система логирования

## Обзор

В приложении реализована расширенная система логирования с поддержкой структурированного формата (JSON) для интеграции с ELK Stack и метрик производительности.

## Настройка

Настройки логирования задаются через переменные окружения или `.env` файл:

```env
# Уровень логирования: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Формат логов: "text" или "json" (для ELK)
LOG_FORMAT=text

# Название сервиса (для идентификации в ELK)
LOG_SERVICE_NAME=mnt-confluence-generator

# Окружение: development, staging, production
LOG_ENVIRONMENT=development

# Максимальный размер лог-файла в МБ
LOG_FILE_MAX_SIZE_MB=100

# Количество резервных копий файлов
LOG_FILE_BACKUP_COUNT=5

# Включить/выключить логирование в файл
LOG_ENABLE_FILE=true

# Включить/выключить логирование в консоль
LOG_ENABLE_CONSOLE=true
```

## Уровни логирования

- **TRACE** (5) - Максимально детальная информация для глубокой отладки
- **DEBUG** (10) - Детальная информация для отладки
- **INFO** (20) - Важные события (создание МНТ, публикация)
- **WARNING** (30) - Предупреждения
- **ERROR** (40) - Ошибки с полным стеком
- **CRITICAL** (50) - Критические ошибки

## Форматы логирования

### Текстовый формат (по умолчанию)

```
2026-01-17 15:30:15 - mnt_generator - INFO - [RequestID=a1b2c3d4 | IP=192.168.1.1 | User=Иванов И.И. | Host=server01 | Service=mnt-confluence-generator | Env=development] МНТ #123 | Создание | Duration: 45.23ms
```

### JSON формат (для ELK)

```json
{
  "timestamp": "2026-01-17T15:30:15.123Z",
  "level": "INFO",
  "logger": "mnt_generator",
  "message": "МНТ #123 | Создание",
  "module": "main",
  "function": "handle_create_form",
  "line": 603,
  "hostname": "server01",
  "service_name": "mnt-confluence-generator",
  "environment": "development",
  "request_id": "a1b2c3d4",
  "user_ip": "192.168.1.1",
  "user_name": "Иванов И.И.",
  "duration_ms": 45.23,
  "request_size_bytes": 1024,
  "response_size_bytes": 2048
}
```

## Автоматически добавляемые поля

### Контекстные поля
- **request_id** - Уникальный идентификатор запроса для трассировки
- **user_ip** - IP адрес пользователя
- **user_name** - Имя пользователя
- **hostname** - Имя хоста сервера
- **service_name** - Название сервиса (из конфига)
- **environment** - Окружение (из конфига)

### Метрики
- **duration_ms** - Время выполнения операции в миллисекундах
- **request_size_bytes** - Размер HTTP запроса в байтах
- **response_size_bytes** - Размер HTTP ответа в байтах
- **status_code** - HTTP статус код (для запросов)

## Что логируется

### 1. HTTP запросы
- Все входящие HTTP запросы (метод, путь, статус)
- Время выполнения запроса
- Размер запроса и ответа
- Уровень логирования зависит от статуса:
  - `ERROR` - для статусов 5xx
  - `WARNING` - для статусов 4xx
  - `DEBUG` - для успешных запросов (2xx, 3xx)

### 2. Действия пользователя
- Открытие страниц (создание, редактирование, список)
- Создание МНТ (с деталями проекта, автора)
- Редактирование МНТ
- Публикация в Confluence
- Сохранение черновиков
- Удаление и восстановление МНТ

### 3. Операции с МНТ
- Создание, обновление, удаление
- Публикация в Confluence
- Ошибки при операциях
- Время выполнения операций

### 4. Операции с Confluence
- Создание страниц
- Обновление страниц
- Загрузка изображений
- Удаление страниц
- Ошибки API
- Время выполнения операций

### 5. Ошибки
- Все исключения с полным стеком вызовов
- Контекст ошибки (request ID, IP, пользователь, окружение)

## Ротация логов

Логи автоматически ротируются по размеру файла:
- Когда файл достигает `LOG_FILE_MAX_SIZE_MB` МБ, создается новая копия
- Старые файлы сохраняются с суффиксом `.1`, `.2`, и т.д.
- Хранится не более `LOG_FILE_BACKUP_COUNT` резервных копий
- Также есть ротация по месяцам (файлы `app_YYYY-MM.log`)

## Интеграция с ELK Stack

### Настройка для отправки в ELK

1. **Установите формат JSON:**
   ```env
   LOG_FORMAT=json
   ```

2. **Filebeat (рекомендуется):**
   
   Создайте конфигурацию `filebeat.yml`:
   ```yaml
   filebeat.inputs:
   - type: log
     enabled: true
     paths:
       - /path/to/logs/app_*.log
     json.keys_under_root: true
     json.add_error_key: true
     fields:
       service: mnt-confluence-generator
       environment: production
     fields_under_root: false
   
   output.logstash:
     hosts: ["logstash-server:5044"]
   ```

3. **Напрямую в Logstash:**
   
   Настройте Logstash для приема JSON логов через TCP/UDP или файлы.

4. **Напрямую в Elasticsearch:**
   
   Можно использовать библиотеку `python-json-logger` с HTTP handler для прямой отправки в Elasticsearch, но Filebeat предпочтительнее.

### Пример запроса в Kibana

После настройки ELK вы сможете выполнять запросы в Kibana:

```
service_name:"mnt-confluence-generator" AND level:"ERROR" AND environment:"production"
```

## Примеры использования

### Простое логирование

```python
from app.logger import logger

logger.info("Простое сообщение")
logger.debug("Отладочная информация")
logger.warning("Предупреждение")
logger.error("Ошибка")
logger.trace("Очень детальная информация")
```

### Логирование с контекстом

```python
from app.logger import log_mnt_operation, log_error, log_request

# Логирование операции с МНТ
log_mnt_operation(
    operation="Создание",
    mnt_id=123,
    user="Иванов И.И.",
    request_id="a1b2c3d4",
    user_ip="192.168.1.1",
    duration_ms=45.23
)

# Логирование ошибки
try:
    # некоторый код
    pass
except Exception as e:
    log_error(
        error=e,
        context="Обработка запроса",
        request_id="a1b2c3d4",
        user_ip="192.168.1.1",
        user_name="Иванов И.И."
    )
```

### Логирование HTTP запроса с метриками

```python
from app.logger import log_request

log_request(
    method="POST",
    path="/mnt/create",
    status_code=200,
    request_id="a1b2c3d4",
    user_ip="192.168.1.1",
    user_name="Иванов И.И.",
    duration_ms=123.45,
    request_size_bytes=2048,
    response_size_bytes=4096
)
```

## Файлы логов

Логи сохраняются в директории `logs/`:
- `app_YYYY-MM.log` - текущий файл логов за месяц
- `app_YYYY-MM.log.1` - предыдущая копия (при ротации по размеру)
- `app_YYYY-MM.log.2` - и т.д.

## Best Practices

1. **Используйте правильные уровни:**
   - `TRACE` - только для глубокой отладки
   - `DEBUG` - для отладки в разработке
   - `INFO` - для важных бизнес-событий
   - `WARNING` - для предупреждений
   - `ERROR` - для всех ошибок

2. **Всегда передавайте контекст:**
   - `request_id` для трассировки запросов
   - `user_ip` и `user_name` для аудита
   - `duration_ms` для мониторинга производительности

3. **Не логируйте чувствительные данные:**
   - Пароли, токены, персональные данные должны быть исключены

4. **Используйте структурированные данные:**
   - В `details` передавайте словари, а не строки для лучшего парсинга в ELK
