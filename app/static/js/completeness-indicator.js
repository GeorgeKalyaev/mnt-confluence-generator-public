/**
 * Модуль для отображения индикатора полноты заполнения МНТ документа
 */

class CompletenessIndicator {
    constructor(formId, mntId = null) {
        this.form = document.querySelector(formId);
        this.mntId = mntId;
        this.indicatorContainer = null;
        this.updateInterval = null;
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        // Создаем контейнер для индикатора
        this.createIndicatorContainer();
        
        // Ждем небольшую задержку, чтобы убедиться, что все элементы DOM загружены
        // и предзаполненные значения уже есть
        setTimeout(() => {
            // Обновляем индикатор при загрузке страницы
            this.updateCompleteness();
        }, 500);
        
        // Обновляем индикатор при изменении полей формы
        this.form.addEventListener('input', () => {
            this.debounceUpdate();
        });
        
        this.form.addEventListener('change', () => {
            this.debounceUpdate();
        });
        
        // Также слушаем события на динамически добавленных элементах таблиц
        const observer = new MutationObserver(() => {
            this.debounceUpdate();
        });
        
        // Наблюдаем за изменениями в форме
        observer.observe(this.form, {
            childList: true,
            subtree: true,
            attributes: false
        });
    }
    
    createIndicatorContainer() {
        // Ищем место для вставки индикатора (после заголовка формы)
        const formTitle = this.form.querySelector('h1') || this.form.querySelector('h2');
        const container = document.createElement('div');
        container.id = 'completeness-indicator';
        container.className = 'completeness-indicator mb-4';
        container.innerHTML = `
            <div class="card border-primary">
                <div class="card-body">
                    <h5 class="card-title mb-3">
                        <i class="bi bi-clipboard-check"></i> Прогресс заполнения документа
                    </h5>
                    <div class="progress mb-3" style="height: 30px;">
                        <div id="completeness-progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%">
                            <span id="completeness-text" class="fw-bold">0%</span>
                        </div>
                    </div>
                    <div id="completeness-details" class="small text-muted">
                        Заполнено: <span id="filled-sections">0</span> из <span id="total-sections">18</span> разделов
                    </div>
                    <div id="incomplete-sections" class="mt-2"></div>
                </div>
            </div>
        `;
        
        if (formTitle) {
            formTitle.parentNode.insertBefore(container, formTitle.nextSibling);
        } else {
            this.form.insertBefore(container, this.form.firstChild);
        }
        
        this.indicatorContainer = container;
    }
    
    async updateCompleteness() {
        try {
            let completeness;
            
            // Всегда собираем данные из формы для актуального состояния
            // Это работает и для создания, и для редактирования
            const formData = new FormData(this.form);
            const data = {};
            
            // Собираем все данные формы (включая confluence_space и confluence_parent_id для проверки полноты)
            for (const [key, value] of formData.entries()) {
                if (key !== 'publish') {  // Исключаем только publish, остальное собираем
                    data[key] = value;
                }
            }
            
            // Также собираем данные напрямую из полей формы (включая textarea и input)
            // Это важно для предзаполненных полей и полей, которые могут не попасть в FormData
            // FormData может не включать пустые поля или предзаполненные значения
            const formElements = this.form.querySelectorAll('input, textarea, select');
            formElements.forEach(element => {
                const name = element.name || element.id;
                if (name && name !== 'publish') {  // Исключаем только publish, остальное собираем (включая confluence_space, confluence_parent_id, tags)
                    if (element.type === 'checkbox') {
                        data[name] = element.checked ? element.value : '';
                    } else if (element.type === 'radio') {
                        if (element.checked) {
                            data[name] = element.value;
                        }
                    } else {
                        // Для textarea и input получаем значение напрямую из DOM
                        // Это гарантирует, что мы получим актуальное значение, включая предзаполненные
                        const value = element.value || '';
                        // Всегда используем значение из DOM, чтобы получить предзаполненные данные
                        data[name] = value;
                    }
                }
            });
            
            // Также собираем данные из скрытых полей таблиц
            const hiddenInputs = this.form.querySelectorAll('input[type="hidden"]');
            hiddenInputs.forEach(input => {
                const name = input.name || input.id;
                if (name && (name.endsWith('_table') || name.includes('_table'))) {
                    data[name] = input.value || '';
                }
            });
            
            // Всегда используем POST для проверки актуальных данных из формы
            // Это работает и для создания, и для редактирования
            const postData = new FormData();
            for (const [key, value] of Object.entries(data)) {
                postData.append(key, value);
            }
            
            const response = await fetch('/api/mnt/completeness', {
                method: 'POST',
                body: postData
            });
            
            if (!response.ok) {
                console.error('CompletenessIndicator: Ошибка проверки полноты', response.status);
                return;
            }
            
            completeness = await response.json();
            
            if (!completeness || !completeness.sections) {
                console.error('CompletenessIndicator: Неверный формат ответа от сервера');
                return;
            }
            
            this.updateIndicator(completeness);
        } catch (error) {
            console.error('Ошибка обновления индикатора полноты:', error);
        }
    }
    
    updateIndicator(completeness) {
        const progressBar = document.getElementById('completeness-progress-bar');
        const progressText = document.getElementById('completeness-text');
        const filledSections = document.getElementById('filled-sections');
        const totalSections = document.getElementById('total-sections');
        const incompleteSections = document.getElementById('incomplete-sections');
        
        if (!progressBar || !progressText) return;
        
        const percentage = completeness.completion_percentage || 0;
        const filled = completeness.filled_sections || 0;
        const total = completeness.total_sections || 18;
        
        // Обновляем прогресс-бар
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
        
        // Обновляем текст
        if (filledSections) filledSections.textContent = filled;
        if (totalSections) totalSections.textContent = total;
        
        // Изменяем цвет в зависимости от процента
        progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger', 'bg-info');
        if (percentage >= 90) {
            progressBar.classList.add('bg-success');
        } else if (percentage >= 50) {
            progressBar.classList.add('bg-info');
        } else if (percentage >= 25) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-danger');
        }
        
        // Обновляем индикаторы в навигации
        if (completeness.sections && completeness.sections.length > 0) {
            this.updateNavigationIndicators(completeness.sections);
        } else {
            console.warn('CompletenessIndicator: No sections data in completeness response');
        }
        
        // Показываем незаполненные разделы
        if (incompleteSections && completeness.sections) {
            const incomplete = completeness.sections.filter(s => !s.filled);
            if (incomplete.length > 0) {
                incompleteSections.innerHTML = `
                    <div class="alert alert-warning mb-0">
                        <strong>Незаполненные разделы:</strong>
                        <ul class="mb-0 mt-2">
                            ${incomplete.map(s => `
                                <li>
                                    <a href="#${s.id}" class="text-decoration-none">${s.name}</a>
                                    ${s.issue ? `<small class="text-muted"> - ${s.issue}</small>` : ''}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            } else {
                incompleteSections.innerHTML = `
                    <div class="alert alert-success mb-0">
                        <i class="bi bi-check-circle"></i> Все разделы заполнены!
                    </div>
                `;
            }
        }
    }
    
    updateNavigationIndicators(sections) {
        if (!sections || sections.length === 0) {
            console.warn('CompletenessIndicator: sections array is empty');
            return;
        }
        
        // Создаем карту статусов заполненности по ID разделов
        const sectionStatusMap = {};
        sections.forEach(section => {
            sectionStatusMap[section.id] = section.filled;
        });
        
        // Обновляем навигацию
        const navItems = document.querySelectorAll('.form-navigation .nav-item[href^="#"]');
        
        navItems.forEach(navItem => {
            const href = navItem.getAttribute('href');
            if (href && href.startsWith('#')) {
                const sectionId = href.substring(1);
                const isFilled = sectionStatusMap[sectionId];
                
                // Удаляем предыдущие классы статуса
                navItem.classList.remove('nav-item-filled', 'nav-item-empty');
                
                // Добавляем соответствующий класс
                if (isFilled !== undefined) {
                    if (isFilled) {
                        navItem.classList.add('nav-item-filled');
                    } else {
                        navItem.classList.add('nav-item-empty');
                    }
                }
            }
        });
        
        // Также обновляем подразделы, которые могут ссылаться на подразделы (3-1, 3-2 и т.д.)
        // Но для них нет отдельных проверок, поэтому они наследуют статус основного раздела
        const subNavItems = document.querySelectorAll('.form-navigation .nav-subsection[href^="#"]');
        subNavItems.forEach(subNavItem => {
            const href = subNavItem.getAttribute('href');
            if (href && href.startsWith('#')) {
                const subSectionId = href.substring(1);
                // Для подразделов проверяем родительский раздел
                // Например, section-3-1 -> проверяем section-3
                const parentSectionId = subSectionId.replace(/-\d+$/, '');
                const parentFilled = sectionStatusMap[parentSectionId];
                
                subNavItem.classList.remove('nav-item-filled', 'nav-item-empty');
                if (parentFilled !== undefined) {
                    if (parentFilled) {
                        subNavItem.classList.add('nav-item-filled');
                    } else {
                        subNavItem.classList.add('nav-item-empty');
                    }
                }
            }
        });
    }
    
    debounceUpdate() {
        // Отменяем предыдущий таймер
        if (this.updateInterval) {
            clearTimeout(this.updateInterval);
        }
        
        // Устанавливаем новый таймер
        this.updateInterval = setTimeout(() => {
            this.updateCompleteness();
        }, 1000); // Обновляем через 1 секунду после последнего изменения
    }
    
    destroy() {
        if (this.updateInterval) {
            clearTimeout(this.updateInterval);
        }
        if (this.indicatorContainer) {
            this.indicatorContainer.remove();
        }
    }
}

// Автоматическая инициализация для форм создания и редактирования
document.addEventListener('DOMContentLoaded', function() {
    // Для формы создания
    const createForm = document.querySelector('form[action*="/mnt/create"]');
    if (createForm) {
        window.completenessIndicator = new CompletenessIndicator('form[action*="/mnt/create"]');
    }
    
    // Для формы редактирования - пробуем найти форму
    const editForm = document.querySelector('form[action*="/edit"]');
    if (editForm) {
        // Извлекаем ID МНТ из URL
        const urlMatch = window.location.pathname.match(/\/mnt\/(\d+)\/edit/);
        const mntId = urlMatch ? parseInt(urlMatch[1]) : null;
        
        // Используем селектор по action формы
        const formAction = editForm.getAttribute('action');
        const formSelector = formAction ? `form[action="${formAction}"]` : 'form[action*="/edit"]';
        
        // Инициализируем индикатор
        window.completenessIndicator = new CompletenessIndicator(formSelector, mntId);
    }
});
