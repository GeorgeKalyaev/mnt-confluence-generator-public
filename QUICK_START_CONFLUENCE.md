# Быстрый старт Confluence для тестирования

## Шаг 1: Убедитесь что Docker Desktop запущен

1. Откройте Docker Desktop из меню Пуск
2. Дождитесь полного запуска (иконка в трее)
3. Откройте **НОВЫЙ** терминал (PowerShell или cmd)

## Шаг 2: Запустите Confluence

Выполните в терминале:

```bash
cd C:\Users\kalya\mnt-confluence-generator
docker run -d --name confluence-test -p 8090:8090 -v confluence-data:/var/atlassian/application-data/confluence atlassian/confluence-server:latest
```

**Что произойдет:**
- Docker автоматически скачает образ Confluence (это займет несколько минут)
- Confluence запустится в контейнере
- Будет доступен на http://localhost:8090

## Шаг 3: Настройте Confluence

1. Откройте браузер: **http://localhost:8090**
2. Дождитесь загрузки (может занять 3-5 минут)
3. Следуйте инструкциям:
   - Выберите "Set it up for me"
   - Создайте администратора (запомните пароль!)
   - Получите trial лицензию: https://my.atlassian.com/
   - Введите лицензионный ключ

## Шаг 4: Создайте Space

1. После настройки создайте Space (например, "TEST")
2. Запомните Space Key (например, "TEST")

## Шаг 5: Обновите .env файл

Откройте файл `.env` и измените:

```env
CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin
CONFLUENCE_PASSWORD=ваш_пароль_который_вы_создали
```

## Шаг 6: Перезапустите ваше приложение

```bash
python -m uvicorn app.main:app --reload
```

## Шаг 7: Проверьте работу

1. Откройте http://localhost:8000/mnt/create
2. Заполните форму
3. Укажите Space Key (например, "TEST")
4. Нажмите "Сохранить и сгенерировать в Confluence"
5. Проверьте, что страница создалась в Confluence!

## Остановка Confluence

```bash
docker stop confluence-test
```

## Запуск снова (после остановки)

```bash
docker start confluence-test
```

## Полезные команды

```bash
# Посмотреть логи
docker logs confluence-test

# Посмотреть статус
docker ps

# Удалить контейнер (если нужно начать заново)
docker stop confluence-test
docker rm confluence-test
```
