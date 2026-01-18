# Быстрая установка Docker для Confluence

## Шаг 1: Установка Docker Desktop

1. Скачайте Docker Desktop для Windows:
   **https://www.docker.com/products/docker-desktop/**

2. Установите Docker Desktop:
   - Запустите установщик
   - Следуйте инструкциям установщика
   - После установки Docker Desktop запустится автоматически
   - Может потребоваться перезагрузка компьютера

3. Проверьте установку:
   ```bash
   docker --version
   ```
   Должно показать версию Docker.

## Шаг 2: Запуск Confluence

### Вариант A: Использовать скрипт (проще)

**Windows (cmd):**
```bash
start-confluence.bat
```

**Windows (PowerShell):**
```powershell
.\start-confluence.ps1
```

### Вариант B: Использовать docker-compose (рекомендуется)

```bash
docker-compose up -d
```

### Вариант C: Команда вручную

```bash
docker run -d --name confluence-test -p 8090:8090 -v confluence-data:/var/atlassian/application-data/confluence atlassian/confluence-server:latest
```

## Шаг 3: Настройка Confluence

1. Откройте браузер: **http://localhost:8090**

2. Дождитесь загрузки (может занять 3-5 минут при первом запуске)

3. Следуйте инструкциям настройки:
   - Выберите "Set it up for me"
   - Создайте администратора (запомните пароль!)
   - Получите trial лицензию: https://my.atlassian.com/
   - Введите лицензионный ключ

4. После настройки создайте Space (например, "TEST")

## Шаг 4: Настройка Confluence в config.py

Откройте файл `app/core/config.py` и обновите настройки Confluence:

```python
# Confluence Configuration
confluence_url: str = "http://localhost:8090"
confluence_username: str = "admin"
confluence_password: str = "ваш_пароль_админа"  # Пароль, который вы установили при настройке Confluence
```

## Шаг 5: Проверка работы

1. Перезапустите ваше приложение:
   ```bash
   python -m uvicorn app:app --reload
   ```

2. Откройте http://localhost:8000/mnt/create

3. Создайте МНТ и попробуйте опубликовать в Confluence

## Остановка Confluence

```bash
docker stop confluence-test
```

## Удаление Confluence (данные сохранятся в volume)

```bash
docker stop confluence-test
docker rm confluence-test
```

## Полное удаление (включая данные)

```bash
docker stop confluence-test
docker rm confluence-test
docker volume rm confluence-data
```

## Полезные команды

```bash
# Посмотреть логи
docker logs confluence-test

# Посмотреть статус
docker ps

# Войти в контейнер
docker exec -it confluence-test bash
```
