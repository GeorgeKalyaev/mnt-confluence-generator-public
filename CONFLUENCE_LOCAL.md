# Локальный Confluence для тестирования

## Вариант 1: Docker (рекомендуется - самый простой)

### Требования:
- Docker Desktop для Windows: https://www.docker.com/products/docker-desktop/

### Быстрый запуск:

1. **Установите Docker Desktop** (если еще не установлен)

2. **Запустите Confluence через Docker:**

```bash
docker run --name confluence-test \
  -p 8090:8090 \
  -e ATL_TOMCAT_MGMTPORT=8091 \
  -e ATL_TOMCAT_PORT=8090 \
  -e ATL_TOMCAT_CONTEXTPATH=/ \
  -v confluence-data:/var/atlassian/application-data/confluence \
  atlassian/confluence-server:latest
```

3. **Дождитесь запуска** (может занять несколько минут)

4. **Откройте в браузере:** http://localhost:8090

5. **Настройка при первом запуске:**
   - Выберите "Set it up for me" (Production Installation)
   - Выберите "External database" → PostgreSQL
   - Или используйте встроенную БД для тестирования (не рекомендуется для production)
   - Создайте административный аккаунт
   - Получите лицензию (можно получить trial на 30 дней): https://my.atlassian.com/

### Настройка в .env файле:

После запуска Confluence, обновите файл `.env`:

```env
CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin
CONFLUENCE_PASSWORD=ваш_пароль_админа
```

**Примечание:** Для Confluence Server используется username/password, а не API token.

---

## Вариант 2: Docker Compose (более удобно)

Создайте файл `docker-compose.yml`:

```yaml
version: '3.8'
services:
  confluence:
    image: atlassian/confluence-server:latest
    container_name: confluence-test
    ports:
      - "8090:8090"
    environment:
      ATL_TOMCAT_MGMTPORT: 8091
      ATL_TOMCAT_PORT: 8090
      ATL_TOMCAT_CONTEXTPATH: /
    volumes:
      - confluence-data:/var/atlassian/application-data/confluence
    restart: unless-stopped

volumes:
  confluence-data:
```

Запуск:
```bash
docker-compose up -d
```

Остановка:
```bash
docker-compose down
```

---

## Вариант 3: Установка Confluence Server (без Docker)

Это более сложный вариант, требующий:
- Java JDK 11+
- PostgreSQL (можно использовать тот же, что для проекта)
- Скачать Confluence Server: https://www.atlassian.com/software/confluence/download

**Не рекомендуется для быстрого тестирования** - лучше использовать Docker.

---

## Получение trial лицензии

1. Перейдите на: https://my.atlassian.com/
2. Зарегистрируйтесь (или войдите)
3. Создайте trial лицензию для Confluence Server
4. Получите лицензионный ключ
5. Введите его при настройке Confluence

---

## Важные замечания

1. **Производительность:** Confluence требует много ресурсов (минимум 2GB RAM)
2. **Лицензия:** Для тестирования можно использовать 30-дневную trial лицензию
3. **Данные:** Данные сохраняются в Docker volume, удаление контейнера не удалит данные
4. **Порт:** По умолчанию Confluence использует порт 8090

---

## Быстрая проверка после запуска

После запуска Confluence:

1. Создайте Space (например, "TEST")
2. Запомните Space Key (например, "TEST")
3. Обновите `.env` файл
4. Перезапустите ваше приложение
5. Попробуйте создать МНТ через форму

---

## Альтернатива: Использовать облачный Confluence

Если у вас есть доступ к облачному Confluence (Confluence Cloud):
- Используйте его URL
- Создайте API Token: https://id.atlassian.com/manage-profile/security/api-tokens
- Настройте в `.env`:
  ```env
  CONFLUENCE_URL=https://your-domain.atlassian.net
  CONFLUENCE_EMAIL=your-email@example.com
  CONFLUENCE_API_TOKEN=your-api-token
  ```
