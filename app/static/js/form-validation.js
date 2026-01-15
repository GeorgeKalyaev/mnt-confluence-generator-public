// Валидация форм МНТ
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form[action*="/mnt/"]');
    if (!form) return;
    
    // Элементы формы
    const projectNameInput = document.getElementById('project_name');
    const authorInput = document.getElementById('author');
    const confluenceSpaceInput = document.getElementById('confluence_space');
    
    // Создаем контейнер для ошибок
    function createErrorElement(field) {
        let errorDiv = field.parentElement.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            field.parentElement.appendChild(errorDiv);
        }
        return errorDiv;
    }
    
    // Показываем ошибку
    function showError(field, message) {
        field.classList.add('is-invalid');
        const errorDiv = createErrorElement(field);
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    // Убираем ошибку
    function clearError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentElement.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }
    
    // Валидация обязательных полей
    function validateRequired(field, fieldName) {
        if (!field.value.trim()) {
            showError(field, `${fieldName} обязательно для заполнения`);
            return false;
        }
        clearError(field);
        return true;
    }
    
    // Валидация при вводе
    if (projectNameInput) {
        projectNameInput.addEventListener('blur', function() {
            validateRequired(this, 'Название проекта');
        });
        
        projectNameInput.addEventListener('input', function() {
            if (this.value.trim()) {
                clearError(this);
            }
        });
    }
    
    if (authorInput) {
        authorInput.addEventListener('blur', function() {
            validateRequired(this, 'Автор');
        });
        
        authorInput.addEventListener('input', function() {
            if (this.value.trim()) {
                clearError(this);
            }
        });
    }
    
    if (confluenceSpaceInput) {
        confluenceSpaceInput.addEventListener('blur', function() {
            validateRequired(this, 'Space Key');
        });
        
        confluenceSpaceInput.addEventListener('input', function() {
            if (this.value.trim()) {
                clearError(this);
            }
        });
    }
    
    // Поле описания изменений (только для формы редактирования)
    const changeDescriptionInput = document.getElementById('change_description');
    const historyChangesTableInput = document.getElementById('history_changes_table');
    
    // Функция для проверки, есть ли изменения в форме (кроме change_description и history_changes_table)
    function hasFormChanges() {
        if (!form) return false;
        
        // Получаем начальные данные формы (сохраняем при загрузке страницы)
        if (!window.initialFormState) {
            window.initialFormState = {};
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                // Игнорируем служебные поля: change_description, history_changes_table, publish_hidden, author
                // (author не учитывается в изменениях, т.к. его изменение не считается изменением МНТ)
                if (input.id === 'change_description' || 
                    input.id === 'history_changes_table' || 
                    input.id === 'publish_hidden' ||
                    input.id === 'author' ||
                    input.type === 'hidden' ||
                    input.type === 'file') {
                    return;
                }
                if (input.type === 'checkbox' || input.type === 'radio') {
                    window.initialFormState[input.name] = input.checked;
                } else {
                    window.initialFormState[input.name] = input.value || '';
                }
            });
            return false; // При первой загрузке изменений нет
        }
        
        // Сравниваем текущие значения с начальными
        const inputs = form.querySelectorAll('input, textarea, select');
        for (let input of inputs) {
            // Игнорируем служебные поля: change_description, history_changes_table, publish_hidden, author
            // (author не учитывается в изменениях, т.к. его изменение не считается изменением МНТ)
            if (input.id === 'change_description' || 
                input.id === 'history_changes_table' || 
                input.id === 'publish_hidden' ||
                input.id === 'author' ||
                input.type === 'hidden' ||
                input.type === 'file') {
                continue;
            }
            
            const currentValue = (input.type === 'checkbox' || input.type === 'radio') ? input.checked : (input.value || '');
            const initialValue = window.initialFormState[input.name];
            
            if (String(currentValue) !== String(initialValue)) {
                return true; // Найдено изменение
            }
        }
        
        return false; // Изменений не найдено
    }
    
    // Сохраняем начальное состояние при загрузке
    if (historyChangesTableInput) {
        // Это форма редактирования - сохраняем начальное состояние
        setTimeout(function() {
            hasFormChanges(); // Вызов сохранит начальное состояние
            updateAuthorAndDescriptionRequirement(); // Обновляем индикатор
        }, 200);
        
        // Отслеживаем изменения в реальном времени
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.id === 'change_description' || 
                input.id === 'history_changes_table' || 
                input.id === 'publish_hidden' ||
                input.type === 'hidden' ||
                input.type === 'file') {
                return;
            }
            
            input.addEventListener('input', function() {
                setTimeout(updateAuthorAndDescriptionRequirement, 100);
            });
            input.addEventListener('change', function() {
                setTimeout(updateAuthorAndDescriptionRequirement, 100);
            });
        });
        
        // Отслеживаем добавление новой строки в таблице истории
        const historyTableTbody = document.getElementById('history_changes_tbody');
        if (historyTableTbody) {
            // Используем MutationObserver для отслеживания изменений в таблице
            const observer = new MutationObserver(function() {
                setTimeout(updateAuthorAndDescriptionRequirement, 100);
            });
            observer.observe(historyTableTbody, { childList: true, subtree: true });
        }
    }
    
    // Функция для обновления требования автора и описания
    function updateAuthorAndDescriptionRequirement() {
        if (!historyChangesTableInput) return;
        
        const hasChanges = hasFormChanges();
        const authorRequiredStar = document.getElementById('author_required_star');
        const historyTableTbody = document.getElementById('history_changes_tbody');
        const hasNewHistoryRow = historyTableTbody ? 
            historyTableTbody.querySelector('tr:has(input[name="history_description_new"])') !== null : false;
        
        if (hasChanges || hasNewHistoryRow) {
            // Есть изменения ИЛИ добавлена новая строка - автор обязателен
            if (authorRequiredStar) {
                authorRequiredStar.style.display = 'inline';
            }
        } else {
            // Изменений нет и новая строка не добавлена - автор не обязателен
            if (authorRequiredStar) {
                authorRequiredStar.style.display = 'none';
            }
            if (authorInput) {
                clearError(authorInput);
            }
        }
    }
    
    // Валидация при отправке формы
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        if (projectNameInput && !validateRequired(projectNameInput, 'Название проекта')) {
            isValid = false;
        }
        
        // Проверяем автора и описание только если есть изменения в форме
        if (historyChangesTableInput) {
            // Это форма редактирования
            const hasChanges = hasFormChanges();
            const historyTableTbody = document.getElementById('history_changes_tbody');
            const hasNewHistoryRow = historyTableTbody ? 
                historyTableTbody.querySelector('tr:has(input[name="history_description_new"])') !== null : false;
            
            if (hasChanges || hasNewHistoryRow) {
                // Есть изменения ИЛИ добавлена новая строка в истории - автор обязателен
                if (authorInput && !authorInput.value.trim()) {
                    showError(authorInput, 'Автор обязателен для заполнения, так как были внесены изменения');
                    isValid = false;
                } else {
                    clearError(authorInput);
                }
                
                // Проверяем описание в новой строке истории (если новая строка добавлена)
                if (hasNewHistoryRow && historyTableTbody) {
                    const descriptionInput = historyTableTbody.querySelector('input[name="history_description_new"]');
                    if (descriptionInput) {
                        if (!descriptionInput.value.trim()) {
                            descriptionInput.classList.add('is-invalid');
                            const descCell = descriptionInput.closest('td');
                            if (descCell) {
                                // Удаляем старые сообщения об ошибках
                                const oldError = descCell.querySelector('.invalid-feedback');
                                if (oldError) oldError.remove();
                                
                                // Добавляем новое сообщение
                                const errorDiv = document.createElement('div');
                                errorDiv.className = 'invalid-feedback';
                                errorDiv.textContent = 'Описание изменений обязательно для заполнения';
                                descCell.appendChild(errorDiv);
                            }
                            isValid = false;
                        } else {
                            descriptionInput.classList.remove('is-invalid');
                            const descCell = descriptionInput.closest('td');
                            if (descCell) {
                                const errorDiv = descCell.querySelector('.invalid-feedback');
                                if (errorDiv) errorDiv.remove();
                            }
                        }
                    }
                }
            } else {
                // Изменений нет и новая строка не добавлена - автор не обязателен
                clearError(authorInput);
            }
        } else {
            // Это форма создания - автор обязателен только если указан
            // (при создании автор обычно указывается всегда)
        }
        
        if (confluenceSpaceInput && !validateRequired(confluenceSpaceInput, 'Space Key')) {
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
            e.stopPropagation();
            
            // Прокручиваем к первой ошибке
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
            
            return false;
        }
        
        // Показываем индикатор загрузки
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = true;
            const originalText = btn.textContent;
            btn.dataset.originalText = originalText;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Сохранение...';
        });
    });
    
    // Восстанавливаем кнопки при ошибке
    form.addEventListener('invalid', function(e) {
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = false;
            if (btn.dataset.originalText) {
                btn.textContent = btn.dataset.originalText;
            }
        });
    }, true);
});
