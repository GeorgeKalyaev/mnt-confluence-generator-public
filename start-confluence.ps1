# Скрипт для запуска Confluence через Docker

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Запуск Confluence через Docker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка наличия Docker
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "[OK] Docker найден: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ОШИБКА] Docker не установлен!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Установите Docker Desktop: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "После установки запустите этот скрипт снова."
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""

# Проверка, не запущен ли уже Confluence
$existing = docker ps -a --filter "name=confluence-test" --format "{{.Names}}" 2>&1
if ($existing -match "confluence-test") {
    Write-Host "Confluence уже существует. Запускаю существующий контейнер..." -ForegroundColor Yellow
    docker start confluence-test
} else {
    Write-Host "Создаю и запускаю новый контейнер Confluence..." -ForegroundColor Yellow
    docker run -d --name confluence-test -p 8090:8090 -v confluence-data:/var/atlassian/application-data/confluence atlassian/confluence-server:latest
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Confluence запускается..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Откройте в браузере: http://localhost:8090" -ForegroundColor Green
Write-Host ""
Write-Host "Первый запуск может занять 3-5 минут." -ForegroundColor Yellow
Write-Host "Дождитесь сообщения 'Confluence is starting up...'"
Write-Host ""
Write-Host "После настройки обновите .env файл:" -ForegroundColor Cyan
Write-Host "  CONFLUENCE_URL=http://localhost:8090"
Write-Host "  CONFLUENCE_USERNAME=admin"
Write-Host "  CONFLUENCE_PASSWORD=ваш_пароль"
Write-Host ""
Read-Host "Нажмите Enter для выхода"
