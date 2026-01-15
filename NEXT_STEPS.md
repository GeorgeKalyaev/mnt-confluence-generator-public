# Следующие шаги после запуска Confluence

## 1. Проверка статуса контейнера

Выполните в терминале:
```bash
docker ps
```

Должен быть виден контейнер `confluence-test` со статусом "Up".

## 2. Откройте Confluence в браузере

Откройте: **http://localhost:8090**

Первый запуск может занять **3-5 минут**. Подождите, пока появится страница настройки.

## 3. Настройка Confluence

### Шаг 3.1: Выбор типа установки
- Выберите **"Set it up for me"** (Production Installation)

### Шаг 3.2: База данных
- Можно использовать **встроенную БД** для тестирования (HSQL Database)
- Или выбрать PostgreSQL (если хотите использовать ваш PostgreSQL)

### Шаг 3.3: Создание администратора
- Создайте административный аккаунт
- **ВАЖНО:** Запомните пароль!

### Шаг 3.4: Лицензия
- Получите trial лицензию (бесплатно на 30 дней):
  1. Перейдите на https://my.atlassian.com/
  2. Зарегистрируйтесь или войдите
  3. Создайте trial лицензию для Confluence Server
  4. Скопируйте лицензионный ключ
  5. Введите его в Confluence

## 4. Создание Space

После настройки:
1. Создайте Space (например, "TEST")
2. **Запомните Space Key** (например, "TEST")
   - Space Key можно найти в URL: `http://localhost:8090/spaces/TEST/...`

## 5. Обновление .env файла

Откройте файл `.env` в папке проекта и измените:

```env
CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin
CONFLUENCE_PASSWORD=ваш_пароль_который_вы_создали
```

**Важно:** Не используйте API Token для локального Confluence Server - используйте username/password!

## 6. Перезапуск вашего приложения

```bash
cd C:\Users\kalya\mnt-confluence-generator
python -m uvicorn app.main:app --reload
```

## 7. Тестирование

1. Откройте http://localhost:8000/mnt/create
2. Заполните форму МНТ
3. В поле "Space Key" укажите ваш Space Key (например, "TEST")
4. Нажмите "Сохранить и сгенерировать в Confluence"
5. Проверьте, что страница создалась в Confluence!

## Полезные команды

```bash
# Посмотреть логи Confluence
docker logs confluence-test

# Остановить Confluence
docker stop confluence-test

# Запустить снова
docker start confluence-test

# Посмотреть статус
docker ps
```
