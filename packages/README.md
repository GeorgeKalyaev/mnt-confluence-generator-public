# Локальные Python зависимости

Эта папка содержит все Python зависимости проекта для **офлайн-установки** в закрытой корпоративной сети.

## Что внутри

Все `.whl` файлы (wheel packages) для установки зависимостей из `requirements.txt` без подключения к интернету.

**Размер:** ~9 МБ  
**Количество файлов:** 29 пакетов (включая транзитивные зависимости)

## Установка из локальной папки

### Windows (cmd/PowerShell):

```bash
pip install --no-index --find-links ./packages -r requirements.txt
```

### Linux/macOS:

```bash
pip install --no-index --find-links ./packages -r requirements.txt
```

**Параметры:**
- `--no-index` - не обращаться к PyPI (не нужен интернет)
- `--find-links ./packages` - искать пакеты в локальной папке `packages/`
- `-r requirements.txt` - установить зависимости из файла requirements.txt

## Обновление зависимостей

Если нужно обновить зависимости в папке `packages/`:

```bash
# Удалить старые файлы
rm -rf packages/*  # Linux/macOS
# или
Remove-Item packages/* -Recurse -Force  # Windows PowerShell

# Скачать заново
pip download -r requirements.txt -d ./packages
```

## Важно

⚠️ **Зависимости зафиксированы для Windows (cp314-win_amd64)**

Если развертывание планируется на Linux или другой платформе, необходимо:
1. Скачать зависимости на целевой платформе
2. Или использовать универсальные пакеты (где возможно)

Для кроссплатформенной установки рекомендуется создать отдельные папки для каждой платформы или использовать Docker.
