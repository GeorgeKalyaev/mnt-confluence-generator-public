# Реализация Drag & Drop и Автодополнения

## 📋 Описание

Документ описывает как интегрировать функциональность Drag & Drop для таблиц и автодополнения для полей в проект МНТ Generator.

## 🎯 1. Drag & Drop для таблиц

### Как это работает:

1. **HTML5 Drag & Drop API** - нативная поддержка браузера
2. **Визуальные индикаторы** - подсветка при перетаскивании
3. **Автоматическое обновление** - синхронизация со скрытым полем после изменения порядка

### Интеграция:

#### Шаг 1: Подключить скрипт в `create.html` и `edit.html`

Добавить перед закрывающим тегом `</body>`:

```html
<script src="{{ url_for('static', path='js/drag-drop-tables.js') }}"></script>
```

#### Шаг 2: Инициализировать для каждой таблицы

Например, для таблицы профилей нагрузки:

```javascript
// После загрузки данных таблицы
let loadProfilesDragDrop = null;

// Инициализация после loadExistingLoadProfilesData()
loadProfilesDragDrop = new TableDragDrop(
    'load_profiles_visual_table',
    'load_profiles_tbody',
    updateLoadProfilesHiddenField // callback для обновления скрытого поля
);

// После добавления новой строки
addLoadProfilesRowBtn.addEventListener('click', function(e) {
    e.preventDefault();
    const newRow = createLoadProfilesRow();
    loadProfilesTableTbody.appendChild(newRow);
    updateLoadProfilesHiddenField();
    
    // Обновляем drag & drop
    if (loadProfilesDragDrop) {
        loadProfilesDragDrop.refresh();
    }
});
```

#### Шаг 3: Добавить CSS стили

Добавить в `base.html` или отдельный CSS файл:

```css
.draggable-row {
    transition: background-color 0.2s;
}

.draggable-row.dragging {
    opacity: 0.5;
    background-color: #f0f0f0;
}

.draggable-row.drag-over-top {
    border-top: 2px solid #2196f3;
}

.draggable-row.drag-over-bottom {
    border-bottom: 2px solid #2196f3;
}

.drag-handle {
    cursor: move !important;
    user-select: none;
    color: #666;
}

.drag-handle:hover {
    color: #2196f3;
}
```

### Пример использования:

```javascript
// Для таблицы контактов
const contactsDragDrop = new TableDragDrop(
    'contacts_visual_table',
    'contacts_tbody',
    updateContactsHiddenField
);
```

---

## ✏️ 2. Автодополнение в полях

### Как это работает:

1. **Локальные списки** - предложения из предопределенных данных
2. **API запросы** - загрузка данных из базы данных
3. **История** - запоминание ранее введенных значений
4. **Подсветка совпадений** - визуальное выделение найденного текста

### Варианты реализации:

#### Вариант A: Автодополнение из локального списка

```javascript
// Для поля "Название проекта"
const projectInput = document.getElementById('project');
initAutocomplete(projectInput, {
    source: ['Проект А', 'Проект Б', 'Проект В', 'Претрейд', 'Тестирование'],
    minLength: 1,
    maxItems: 10
});
```

#### Вариант B: Автодополнение из API (существующие проекты)

```javascript
// Создать endpoint в main.py
@app.get("/api/autocomplete/projects")
async def get_projects_autocomplete(db: Session = Depends(get_db)):
    projects = db.execute(
        text("SELECT DISTINCT project FROM mnt.documents WHERE project IS NOT NULL ORDER BY project")
    ).fetchall()
    return [row[0] for row in projects]

// В JavaScript
const projectInput = document.getElementById('project');
initAutocomplete(projectInput, {
    source: async () => {
        return await fetchAutocompleteData('/api/autocomplete/projects');
    },
    minLength: 1,
    fetchOnFocus: true
});
```

#### Вариант C: Автодополнение для авторов

```javascript
// Endpoint в main.py
@app.get("/api/autocomplete/authors")
async def get_authors_autocomplete(db: Session = Depends(get_db)):
    authors = db.execute(
        text("SELECT DISTINCT author FROM mnt.documents WHERE author IS NOT NULL ORDER BY author")
    ).fetchall()
    return [row[0] for row in authors]

// В JavaScript
const authorInput = document.getElementById('author');
initAutocomplete(authorInput, {
    source: async () => {
        return await fetchAutocompleteData('/api/autocomplete/authors');
    },
    minLength: 1
});
```

#### Вариант D: Автодополнение для тегов

```javascript
// Endpoint в main.py
@app.get("/api/autocomplete/tags")
async def get_tags_autocomplete(db: Session = Depends(get_db)):
    # Получаем все теги из JSONB поля
    result = db.execute(
        text("""
            SELECT DISTINCT jsonb_array_elements_text(data_json->'tags') as tag
            FROM mnt.documents
            WHERE data_json->'tags' IS NOT NULL
            ORDER BY tag
        """)
    ).fetchall()
    return [row[0] for row in result if row[0]]

// В JavaScript - для поля тегов с поддержкой множественного ввода
const tagsInput = document.getElementById('tags');
initAutocomplete(tagsInput, {
    source: async () => {
        return await fetchAutocompleteData('/api/autocomplete/tags');
    },
    minLength: 1,
    onSelect: (item, input) => {
        // Для тегов - добавляем через запятую если уже есть значения
        const currentValue = input.value.trim();
        const newTag = typeof item === 'string' ? item : item.value;
        
        if (currentValue && !currentValue.endsWith(',')) {
            input.value = currentValue + ', ' + newTag;
        } else {
            input.value = currentValue + newTag;
        }
    }
});
```

### Интеграция:

#### Шаг 1: Подключить скрипт

Добавить в `create.html` и `edit.html`:

```html
<script src="{{ url_for('static', path='js/autocomplete.js') }}"></script>
```

#### Шаг 2: Инициализировать для нужных полей

В конце JavaScript блока формы:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Автодополнение для проектов
    const projectInput = document.getElementById('project');
    if (projectInput) {
        initAutocomplete(projectInput, {
            source: async () => {
                const response = await fetch('/api/autocomplete/projects');
                const data = await response.json();
                return data;
            },
            minLength: 1,
            fetchOnFocus: true
        });
    }
    
    // Автодополнение для авторов
    const authorInput = document.getElementById('author');
    if (authorInput) {
        initAutocomplete(authorInput, {
            source: async () => {
                const response = await fetch('/api/autocomplete/authors');
                const data = await response.json();
                return data;
            },
            minLength: 1
        });
    }
    
    // Автодополнение для тегов (с поддержкой множественного ввода)
    const tagsInput = document.getElementById('tags');
    if (tagsInput) {
        initAutocomplete(tagsInput, {
            source: async () => {
                const response = await fetch('/api/autocomplete/tags');
                const data = await response.json();
                return data;
            },
            minLength: 1,
            onSelect: (item, input) => {
                const currentValue = input.value.trim();
                const parts = currentValue.split(',').map(s => s.trim()).filter(s => s);
                const newTag = typeof item === 'string' ? item : item.value;
                
                if (!parts.includes(newTag)) {
                    parts.push(newTag);
                }
                
                input.value = parts.join(', ');
                input.focus();
            }
        });
    }
});
```

---

## 🎨 Визуальные улучшения

### Иконки для drag & drop:

Можно использовать более современные иконки:

```css
.drag-handle::before {
    content: '⋮⋮';
    font-size: 1.2em;
    letter-spacing: -2px;
}
```

Или использовать SVG:

```html
<svg width="16" height="16" viewBox="0 0 16 16">
    <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="2"/>
</svg>
```

---

## ✅ Преимущества

### Drag & Drop:
- ✅ Интуитивный интерфейс
- ✅ Быстрое изменение порядка строк
- ✅ Визуальная обратная связь
- ✅ Работает на мобильных устройствах (touch events можно добавить)

### Автодополнение:
- ✅ Ускорение ввода данных
- ✅ Снижение опечаток
- ✅ Единообразие данных (использование существующих значений)
- ✅ Улучшенный UX

---

## 🔧 Настройка и расширение

### Кастомизация автодополнения:

```javascript
// Кастомный рендеринг элементов
initAutocomplete(input, {
    source: [...],
    renderItem: (item) => {
        return `<div>
            <strong>${item.name}</strong>
            <small>${item.project}</small>
        </div>`;
    }
});
```

### Touch события для мобильных (Drag & Drop):

Можно использовать библиотеку `SortableJS` для полной поддержки touch-устройств:

```javascript
import Sortable from 'sortablejs';

Sortable.create(tbody, {
    handle: '.drag-handle',
    animation: 150,
    onEnd: function() {
        updateHiddenField();
    }
});
```

---

## 📝 Пример полной интеграции

См. файлы:
- `app/static/js/drag-drop-tables.js` - реализация drag & drop
- `app/static/js/autocomplete.js` - реализация автодополнения

Для применения - следуйте инструкциям выше по интеграции в шаблоны.