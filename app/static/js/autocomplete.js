/**
 * Система автодополнения для полей формы МНТ
 * Поддерживает:
 * - Автодополнение из существующих данных БД
 * - Локальные списки предложений
 * - История введенных значений
 */

class MNTAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            source: options.source || [], // Массив строк или функция для получения данных
            minLength: options.minLength || 2, // Минимальная длина для показа подсказок
            maxItems: options.maxItems || 10, // Максимум элементов в списке
            caseSensitive: options.caseSensitive || false,
            highlight: options.highlight !== false, // Подсветка совпадающего текста
            onSelect: options.onSelect || null, // Callback при выборе элемента
            fetchOnFocus: options.fetchOnFocus || false, // Загружать данные при фокусе
            ...options
        };
        
        this.container = null;
        this.dropdown = null;
        this.selectedIndex = -1;
        this.filteredItems = [];
        
        this.init();
    }
    
    init() {
        if (!this.input) return;
        
        // Создаем контейнер для выпадающего списка
        this.createDropdown();
        
        // Устанавливаем обработчики событий
        this.setupEventListeners();
        
        // Загружаем данные если указан URL или функция
        if (typeof this.options.source === 'function') {
            this.loadData();
        }
    }
    
    createDropdown() {
        // Создаем контейнер для автодополнения
        this.container = document.createElement('div');
        this.container.className = 'autocomplete-container';
        this.container.style.cssText = 'position: relative; width: 100%;';
        
        // Создаем выпадающий список
        this.dropdown = document.createElement('ul');
        this.dropdown.className = 'autocomplete-dropdown';
        this.dropdown.style.cssText = `
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            background: white;
            border: 1px solid #ced4da;
            border-radius: 0.375rem;
            max-height: 200px;
            overflow-y: auto;
            list-style: none;
            padding: 0;
            margin: 2px 0 0 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        
        // Обертываем input в контейнер
        const parent = this.input.parentNode;
        if (parent) {
            parent.insertBefore(this.container, this.input.nextSibling);
            this.container.appendChild(this.dropdown);
        }
        
        // Добавляем стили если их еще нет
        this.injectStyles();
    }
    
    injectStyles() {
        if (document.getElementById('autocomplete-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'autocomplete-styles';
        style.textContent = `
            .autocomplete-dropdown li {
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .autocomplete-dropdown li:hover,
            .autocomplete-dropdown li.active {
                background-color: #f8f9fa;
            }
            
            .autocomplete-dropdown li:last-child {
                border-bottom: none;
            }
            
            .autocomplete-dropdown li .highlight {
                font-weight: bold;
                background-color: #fff3cd;
            }
            
            .autocomplete-dropdown li.no-results {
                color: #6c757d;
                font-style: italic;
                cursor: default;
            }
            
            .autocomplete-dropdown li.no-results:hover {
                background-color: transparent;
            }
        `;
        document.head.appendChild(style);
    }
    
    setupEventListeners() {
        // Обработчик ввода текста
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
        
        // Обработчик фокуса
        if (this.options.fetchOnFocus) {
            this.input.addEventListener('focus', () => {
                this.loadData();
            });
        }
        
        // Обработчик клавиатуры
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
        
        // Скрываем список при клике вне его
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target) && e.target !== this.input) {
                this.hideDropdown();
            }
        });
    }
    
    async loadData() {
        if (typeof this.options.source === 'function') {
            try {
                const data = await this.options.source();
                this.options.source = Array.isArray(data) ? data : [];
            } catch (error) {
                console.error('Ошибка загрузки данных для автодополнения:', error);
            }
        }
    }
    
    handleInput(value) {
        const query = this.options.caseSensitive ? value : value.toLowerCase();
        
        if (query.length < this.options.minLength) {
            this.hideDropdown();
            return;
        }
        
        // Фильтруем элементы
        this.filteredItems = this.filterItems(query);
        
        if (this.filteredItems.length === 0) {
            this.showNoResults();
        } else {
            this.showDropdown(this.filteredItems);
        }
    }
    
    filterItems(query) {
        const items = Array.isArray(this.options.source) ? this.options.source : [];
        const queryLower = this.options.caseSensitive ? query : query.toLowerCase();
        
        return items
            .filter(item => {
                const text = this.getItemText(item);
                const textLower = this.options.caseSensitive ? text : text.toLowerCase();
                return textLower.includes(queryLower);
            })
            .slice(0, this.options.maxItems);
    }
    
    getItemText(item) {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') return item.text || item.label || item.value || '';
        return String(item);
    }
    
    getItemValue(item) {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') return item.value || item.text || item.label || '';
        return String(item);
    }
    
    showDropdown(items) {
        this.dropdown.innerHTML = '';
        this.selectedIndex = -1;
        
        items.forEach((item, index) => {
            const li = document.createElement('li');
            const itemText = this.getItemText(item);
            const itemValue = this.getItemValue(item);
            
            if (this.options.highlight && this.input.value) {
                li.innerHTML = this.highlightMatch(itemText, this.input.value);
            } else {
                li.textContent = itemText;
            }
            
            li.dataset.value = itemValue;
            li.dataset.index = index;
            
            li.addEventListener('click', () => {
                this.selectItem(item);
            });
            
            this.dropdown.appendChild(li);
        });
        
        this.dropdown.style.display = 'block';
    }
    
    showNoResults() {
        this.dropdown.innerHTML = '<li class="no-results">Нет совпадений</li>';
        this.dropdown.style.display = 'block';
    }
    
    highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.selectedIndex = -1;
    }
    
    handleKeyDown(e) {
        const items = this.dropdown.querySelectorAll('li:not(.no-results)');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                this.highlightItem(items);
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.highlightItem(items);
                break;
                
            case 'Enter':
                if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
                    e.preventDefault();
                    const value = items[this.selectedIndex].dataset.value;
                    this.selectItem(value);
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }
    
    highlightItem(items) {
        items.forEach((li, index) => {
            li.classList.toggle('active', index === this.selectedIndex);
        });
    }
    
    selectItem(item) {
        const value = typeof item === 'string' ? item : this.getItemValue(item);
        this.input.value = value;
        this.hideDropdown();
        
        // Вызываем callback если указан
        if (this.options.onSelect) {
            this.options.onSelect(item, this.input);
        }
        
        // Триггерим событие для других обработчиков
        this.input.dispatchEvent(new Event('autocomplete-select', { bubbles: true }));
    }
}

// Фабричная функция для быстрой инициализации автодополнения
function initAutocomplete(inputSelector, options) {
    const input = typeof inputSelector === 'string' 
        ? document.querySelector(inputSelector) 
        : inputSelector;
    
    if (!input) return null;
    
    return new MNTAutocomplete(input, options);
}

// Функция для получения данных из API
async function fetchAutocompleteData(url, field = 'name') {
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (Array.isArray(data)) {
            return data.map(item => ({
                text: item[field] || item.name || item.title || '',
                value: item[field] || item.name || item.title || '',
                ...item
            }));
        }
        
        return [];
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        return [];
    }
}

// Экспорт
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MNTAutocomplete, initAutocomplete, fetchAutocompleteData };
}

// Делаем доступным глобально для использования в шаблонах
window.MNTAutocomplete = MNTAutocomplete;
window.initAutocomplete = initAutocomplete;
window.fetchAutocompleteData = fetchAutocompleteData;