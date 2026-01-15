# Решение проблемы Docker 500 Internal Server Error

## Проблема
Ошибка: `request returned 500 Internal Server Error for API route`

## Решения (попробуйте по порядку):

### 1. Перезапустите Docker Desktop
- Закройте Docker Desktop полностью
- Запустите снова
- Дождитесь полного запуска (иконка в трее перестанет мигать)

### 2. Проверьте WSL 2
Docker Desktop на Windows требует WSL 2. Проверьте:
```powershell
wsl --status
```

Если WSL не установлен или не версия 2:
```powershell
wsl --install
```

### 3. Обновите Docker Desktop
- Откройте Docker Desktop
- Settings → General
- Проверьте обновления

### 4. Перезагрузите компьютер
Иногда помогает полная перезагрузка после установки Docker.

### 5. Альтернатива: Использовать более старую версию образа
Если проблема сохраняется, попробуйте конкретную версию:
```bash
docker run -d --name confluence-test -p 8090:8090 -v confluence-data:/var/atlassian/application-data/confluence atlassian/confluence-server:8.5.0
```
