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
    
    // Валидация при отправке формы
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        if (projectNameInput && !validateRequired(projectNameInput, 'Название проекта')) {
            isValid = false;
        }
        
        if (authorInput && !validateRequired(authorInput, 'Автор')) {
            isValid = false;
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
