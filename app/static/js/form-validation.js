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
    
    // Проверка обязательных полей разделов 3-15 перед публикацией
    function validateSections3To15() {
        const errors = [];
        
        // Список обязательных полей (разделы 3-15)
        const requiredFields = [
            { id: 'abbreviations_table', name: '3.1 Сокращения (таблица)', isTable: true },
            { id: 'terminology_table', name: '3.2 Терминология (таблица)', isTable: true },
            { id: 'introduction_text', name: '4. Введение', isTable: false },
            { id: 'goals_business', name: '5.1 Цели НТ (бизнес)', isTable: false },
            { id: 'goals_technical', name: '5.1 Цели НТ (технические)', isTable: false },
            { id: 'tasks_nt', name: '5.2 Задачи НТ', isTable: false },
            { id: 'limitations_list', name: '6.1 Ограничения НТ', isTable: false },
            { id: 'risks_table', name: '6.2 Риски НТ (таблица)', isTable: true },
            { id: 'object_general', name: '7.1 Общие сведения', isTable: false },
            { id: 'performance_requirements', name: '7.2 Требования к производительности', isTable: false },
            { id: 'component_architecture_text', name: '7.3.1 Компонентная архитектура', isTable: false },
            { id: 'test_stand_architecture_text', name: '8.1 Архитектура тестового стенда', isTable: false },
            { id: 'planned_tests_intro', name: '9. Стратегия тестирования (вводный текст)', isTable: false },
            { id: 'planned_tests_table', name: '9.1 Планируемые тесты (таблица)', isTable: true },
            { id: 'completion_conditions', name: '9.2 Условия завершения НТ', isTable: false },
            { id: 'database_preparation_text', name: '10. Наполнение БД', isTable: false },
            { id: 'load_modeling_principles', name: '11.1 Общие принципы моделирования нагрузки', isTable: false },
            { id: 'load_profiles_intro', name: '11.2 Профили нагрузки (вводный текст)', isTable: false },
            { id: 'load_profiles_table', name: '11.2 Профили нагрузки (таблица)', isTable: true },
            { id: 'use_scenarios_intro', name: '11.3 Сценарии использования (вводный текст)', isTable: false },
            { id: 'use_scenarios_table', name: '11.3 Сценарии использования (таблица)', isTable: true },
            { id: 'emulators_description', name: '11.4 Описание работы эмуляторов', isTable: false },
            { id: 'monitoring_intro', name: '12. Мониторинг (вводный текст)', isTable: false },
            { id: 'monitoring_tools_intro', name: '12.1 Средства мониторинга (вводный текст)', isTable: false },
            { id: 'monitoring_tools_table', name: '12.1 Средства мониторинга (таблица)', isTable: true },
            { id: 'system_resources_intro', name: '12.2.1 Мониторинг системных ресурсов (вводный текст)', isTable: false },
            { id: 'system_resources_table', name: '12.2.1 Мониторинг системных ресурсов (таблица)', isTable: true },
            { id: 'business_metrics_intro', name: '12.2.2 Мониторинг бизнес-метрик (вводный текст)', isTable: false },
            { id: 'business_metrics_table', name: '12.2.2 Мониторинг бизнес-метрик (таблица)', isTable: true },
            { id: 'customer_requirements_list', name: '13. Требования к Заказчику', isTable: false },
            { id: 'deliverables_intro', name: '14. Материалы, подлежащие сдаче (вводный текст)', isTable: false },
            { id: 'deliverables_table', name: '14. Материалы, подлежащие сдаче (таблица)', isTable: true },
            { id: 'deliverables_working_docs_table', name: '14. Рабочие документы (таблица)', isTable: true },
            { id: 'contacts_table', name: '15. Контакты (таблица)', isTable: true }
        ];
        
        // Проверяем поля
        requiredFields.forEach(field => {
            const element = document.getElementById(field.id);
            if (!element) {
                // Поле не найдено - пропускаем
                return;
            }
            
            let value = element.value ? element.value.trim() : '';
            let isEmpty = false;
            
            if (field.isTable) {
                // Для таблиц: проверяем, что есть данные (не только заголовок)
                // Формат таблицы: "Заголовок1|Заголовок2\nДанные1|Данные2\n..."
                
                // Сначала пытаемся проверить скрытое поле
                if (!value) {
                    // Если скрытое поле пустое, проверяем визуальную таблицу напрямую
                    // Ищем соответствующую визуальную таблицу по ID поля
                    const tableId = field.id.replace('_table', '_visual_table');
                    const visualTable = document.getElementById(tableId);
                    if (visualTable) {
                        const tbody = visualTable.querySelector('tbody');
                        if (tbody) {
                            const rows = tbody.querySelectorAll('tr');
                            // Проверяем, что есть хотя бы одна строка с данными
                            let hasDataRow = false;
                            for (let row of rows) {
                                const inputs = row.querySelectorAll('input, textarea');
                                for (let input of inputs) {
                                    if (input.value && input.value.trim() && input.value.trim() !== '-') {
                                        hasDataRow = true;
                                        break;
                                    }
                                }
                                if (hasDataRow) break;
                            }
                            if (!hasDataRow) {
                                isEmpty = true;
                            }
                        } else {
                            isEmpty = true;
                        }
                    } else {
                        isEmpty = true;
                    }
                } else {
                    // Проверяем, что есть хотя бы одна строка данных (не только заголовок)
                    const lines = value.split('\n').filter(line => line.trim());
                    if (lines.length <= 1) {
                        // Только заголовок, нет данных - проверяем визуальную таблицу
                        const tableId = field.id.replace('_table', '_visual_table');
                        const visualTable = document.getElementById(tableId);
                        if (visualTable) {
                            const tbody = visualTable.querySelector('tbody');
                            if (tbody) {
                                const rows = tbody.querySelectorAll('tr');
                                let hasDataRow = false;
                                for (let row of rows) {
                                    const inputs = row.querySelectorAll('input, textarea');
                                    for (let input of inputs) {
                                        if (input.value && input.value.trim() && input.value.trim() !== '-') {
                                            hasDataRow = true;
                                            break;
                                        }
                                    }
                                    if (hasDataRow) break;
                                }
                                if (!hasDataRow) {
                                    isEmpty = true;
                                }
                            } else {
                                isEmpty = true;
                            }
                        } else {
                            isEmpty = true;
                        }
                    } else {
                        // Проверяем, что есть хотя бы одна строка с данными (не пустая после разделения на колонки)
                        let hasDataRow = false;
                        for (let i = 1; i < lines.length; i++) {
                            const columns = lines[i].split('|').map(col => col.trim()).filter(col => col);
                            if (columns.length > 0 && columns.some(col => col && col !== '-' && col !== '')) {
                                hasDataRow = true;
                                break;
                            }
                        }
                        if (!hasDataRow) {
                            isEmpty = true;
                        }
                    }
                }
            } else {
                // Для текстовых полей: проверяем, что значение не пустое
                // Также проверяем, что это не только дефолтные значения типа "-" или "•-"
                if (!value) {
                    isEmpty = true;
                } else {
                    // Убираем маркеры списков и проверяем наличие реального текста
                    const cleanValue = value
                        .replace(/^[•\-\d+\.]\s*/gm, '') // Убираем маркеры списков
                        .replace(/^-\s*$/gm, '') // Убираем строки с только "-"
                        .replace(/^•-\s*$/gm, '') // Убираем строки с "•-"
                        .trim();
                    
                    if (!cleanValue || cleanValue.length === 0) {
                        isEmpty = true;
                    }
                }
            }
            
            if (isEmpty) {
                console.log(`[VALIDATION] Поле "${field.name}" (${field.id}) пустое или не заполнено`);
                errors.push({ field: element, name: field.name });
            } else {
                console.log(`[VALIDATION] Поле "${field.name}" (${field.id}) заполнено`);
            }
        });
        
        if (errors.length > 0) {
            console.log(`[VALIDATION] Найдено ${errors.length} незаполненных обязательных полей:`, errors.map(e => e.name));
        }
        
        return errors;
    }
    
    // Функция для обновления всех скрытых полей таблиц из визуальных таблиц
    function updateAllTableHiddenFields() {
        // Список функций обновления (они определены в других скриптах)
        const updateFunctions = [
            'updateLoadProfilesHiddenField',
            'updateUseScenariosHiddenField',
            'updateAbbreviationsHiddenField',
            'updateTerminologyHiddenField',
            'updateRisksHiddenField',
            'updatePlannedTestsHiddenField',
            'updateDatabasePreparationHiddenField',
            'updateMonitoringToolsHiddenField',
            'updateSystemResourcesHiddenField',
            'updateBusinessMetricsHiddenField',
            'updateDeliverablesHiddenField',
            'updateDeliverablesWorkingDocsHiddenField',
            'updateContactsHiddenField',
            'updateStandComparisonHiddenField'
        ];
        
        updateFunctions.forEach(funcName => {
            if (typeof window[funcName] === 'function') {
                try {
                    window[funcName]();
                } catch (e) {
                    console.warn(`Ошибка при обновлении ${funcName}:`, e);
                }
            }
        });
    }
    
    // Валидация при отправке формы
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        // Проверяем, публикуем ли мы в Confluence
        const publishHidden = document.getElementById('publish_hidden');
        const isPublishing = publishHidden && publishHidden.value === '1';
        
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
        
        // Дополнительная валидация разделов 3-15 при публикации в Confluence
        if (isPublishing) {
            // Перед валидацией обновляем все скрытые поля таблиц из визуальных таблиц
            // Это нужно, чтобы данные из визуальных таблиц попали в скрытые поля
            updateAllTableHiddenFields();
            
            const sectionErrors = validateSections3To15();
            if (sectionErrors.length > 0) {
                isValid = false;
                
                // Показываем ошибки
                sectionErrors.forEach(error => {
                    if (error.field.type === 'hidden') {
                        // Для скрытых полей ищем связанную таблицу или элемент
                        const fieldId = error.field.id;
                        // Пытаемся найти связанный визуальный элемент
                        let visualElement = document.querySelector(`[data-table-field="${fieldId}"]`);
                        if (!visualElement) {
                            // Ищем родительский form-section
                            const section = error.field.closest('.form-section');
                            if (section) {
                                visualElement = section.querySelector('h3, h4, h5') || section;
                            }
                        }
                        if (visualElement) {
                            // Добавляем класс ошибки к секции
                            visualElement.closest('.form-section')?.classList.add('border-danger', 'border-2', 'p-2');
                        }
                    } else {
                        showError(error.field, `${error.name} обязательно для заполнения перед публикацией`);
                    }
                });
                
                // Показываем общее предупреждение
                alert('⚠ Не все обязательные поля заполнены!\n\nПеред публикацией в Confluence необходимо заполнить все обязательные поля разделов 3-15.\n\nВы можете сохранить МНТ как черновик и заполнить недостающие поля позже.');
            }
        }
        
        if (!isValid) {
            e.preventDefault();
            e.stopPropagation();
            
            // Прокручиваем к первой ошибке
            const firstError = form.querySelector('.is-invalid, .border-danger');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                if (firstError.tagName === 'INPUT' || firstError.tagName === 'TEXTAREA') {
                    firstError.focus();
                }
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
