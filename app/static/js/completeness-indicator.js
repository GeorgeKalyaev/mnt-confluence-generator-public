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
        
        // Обновляем индикатор при загрузке страницы
        this.updateCompleteness();
        
        // Обновляем индикатор при изменении полей формы
        this.form.addEventListener('input', () => {
            this.debounceUpdate();
        });
        
        this.form.addEventListener('change', () => {
            this.debounceUpdate();
        });
        
        // Также слушаем события на динамически добавленных элементах таблиц
        document.addEventListener('DOMNodeInserted', () => {
            this.debounceUpdate();
        }, false);
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
                        Заполнено: <span id="filled-sections">0</span> из <span id="total-sections">15</span> разделов
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
            
            // Собираем все данные формы
            for (const [key, value] of formData.entries()) {
                if (key !== 'confluence_space' && key !== 'confluence_parent_id' && key !== 'publish') {
                    data[key] = value;
                }
            }
            
            // Также собираем данные из скрытых полей таблиц
            const hiddenInputs = this.form.querySelectorAll('input[type="hidden"]');
            hiddenInputs.forEach(input => {
                if (input.id && input.id.endsWith('_table')) {
                    data[input.id] = input.value || '';
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
                console.error('Ошибка проверки полноты');
                return;
            }
            
            completeness = await response.json();
            
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
        const total = completeness.total_sections || 15;
        
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
