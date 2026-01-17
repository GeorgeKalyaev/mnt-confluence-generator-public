# Офлайн зависимости

Проект полностью автономен и не требует подключения к интернету во время работы.

## Внешние зависимости, которые были локализованы

### ✅ Bootstrap 5.3.0
- **CSS**: `app/static/css/bootstrap.min.css`
- **JS**: `app/static/js/vendor/bootstrap.bundle.min.js`

Эти файлы скачаны локально и подключены через `url_for()` в шаблонах.

### ✅ Шрифты
Используются системные шрифты (не требуют интернета):
- `-apple-system` (macOS/iOS)
- `BlinkMacSystemFont` (Chrome на macOS)
- `Segoe UI` (Windows)
- `Roboto` (Android)
- `Helvetica Neue`, `Arial`, `sans-serif` (fallback)

Google Fonts удалены из шаблонов.

## Python зависимости

Все зависимости из `requirements.txt` устанавливаются через PyPI. Для полностью офлайн установки рекомендуется:

1. **Создать локальное зеркало PyPI** в корпоративной сети
2. **Или использовать `pip download`** для скачивания всех пакетов:
   ```bash
   pip download -r requirements.txt -d ./packages
   pip install --no-index --find-links ./packages -r requirements.txt
   ```

## Проверка офлайн-режима

Для проверки что проект не зависит от интернета:

1. Отключите интернет на машине разработки
2. Запустите приложение: `python -m uvicorn app.main:app --reload`
3. Откройте в браузере: http://localhost:8000
4. Проверьте что все стили и скрипты загружаются корректно

Все ресурсы должны загружаться локально из `app/static/`.

---

**Примечание**: Если Bootstrap файлы отсутствуют или повреждены, их можно скачать заново:
- CSS: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
- JS: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
