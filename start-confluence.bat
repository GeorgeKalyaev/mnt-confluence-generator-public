@echo off
echo ========================================
echo Запуск Confluence через Docker
echo ========================================
echo.

REM Проверка наличия Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Docker не установлен!
    echo.
    echo Установите Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo После установки запустите этот скрипт снова.
    pause
    exit /b 1
)

echo [OK] Docker найден
echo.

REM Проверка, не запущен ли уже Confluence
docker ps -a --filter "name=confluence-test" --format "{{.Names}}" | findstr /C:"confluence-test" >nul
if not errorlevel 1 (
    echo Confluence уже существует. Запускаю существующий контейнер...
    docker start confluence-test
) else (
    echo Создаю и запускаю новый контейнер Confluence...
    docker run -d --name confluence-test -p 8090:8090 -v confluence-data:/var/atlassian/application-data/confluence atlassian/confluence-server:latest
)

echo.
echo ========================================
echo Confluence запускается...
echo ========================================
echo.
echo Откройте в браузере: http://localhost:8090
echo.
echo Первый запуск может занять 3-5 минут.
echo Дождитесь сообщения "Confluence is starting up..."
echo.
echo После настройки обновите .env файл:
echo   CONFLUENCE_URL=http://localhost:8090
echo   CONFLUENCE_USERNAME=admin
echo   CONFLUENCE_PASSWORD=ваш_пароль
echo.
pause
