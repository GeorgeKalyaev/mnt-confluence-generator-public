/**
 * Подсветка измененных полей в форме редактирования
 */

(function() {
    'use strict';
    
    // Функция для отправки логов на сервер
    function logToServer(level, message, context) {
        try {
            fetch('/api/log/client', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    level: level,
                    message: message,
                    context: context || {}
                })
            }).catch(function(err) {
                console.error('Ошибка отправки лога на сервер:', err);
            });
        } catch (e) {
            console.error('Ошибка логирования:', e);
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        // Получаем данные о неопубликованных изменениях из data-атрибута или переменной
        const changesScript = document.getElementById('unpublished-changes-data');
        if (!changesScript) {
            const msg = '[highlight-changes] Скрипт с данными изменений не найден';
            console.log(msg);
            logToServer('DEBUG', msg);
            return;
        }
        
        let unpublishedChanges = [];
        try {
            unpublishedChanges = JSON.parse(changesScript.textContent);
            const msg = `[highlight-changes] Загружено изменений: ${unpublishedChanges.length}`;
            console.log(msg, unpublishedChanges);
            logToServer('DEBUG', msg, { count: unpublishedChanges.length });
        } catch (e) {
            const errorMsg = `[highlight-changes] Ошибка парсинга данных изменений: ${e.message}`;
            console.error(errorMsg, changesScript.textContent);
            logToServer('ERROR', errorMsg, { error: e.message });
            return;
        }
        
        if (!unpublishedChanges || unpublishedChanges.length === 0) {
            const msg = '[highlight-changes] Нет изменений для подсветки';
            console.log(msg);
            logToServer('DEBUG', msg);
            return;
        }
        
        const msg = `[highlight-changes] Начинаю подсветку ${unpublishedChanges.length} измененных полей`;
        console.log(msg);
        logToServer('INFO', msg, { count: unpublishedChanges.length });
        
        // Маппинг имен полей на ID/name элементов формы
        const fieldMapping = {
            'project_name': 'project_name',
            'organization_name': 'organization_name',
            'system_version': 'system_version',
            'title': 'project_name', // title маппится на project_name
            'author': 'author',
            'introduction_text': 'introduction_text',
            'object_general': 'object_general',
            'test_stand_architecture_text': 'test_stand_architecture_text',
            'component_architecture_text': 'component_architecture_text',
            'database_preparation_text': 'database_preparation_text',
            'load_modeling_principles': 'load_modeling_principles',
            'emulators_description': 'emulators_description',
            'monitoring_intro': 'monitoring_intro',
            'monitoring_tools_note': 'monitoring_tools_note',
            'system_resources_intro': 'system_resources_intro',
            'business_metrics_intro': 'business_metrics_intro',
            'customer_requirements_intro': 'customer_requirements_intro',
            'customer_requirements_note_intro': 'customer_requirements_note_intro',
            'deliverables_intro': 'deliverables_intro',
            'load_profiles_intro': 'load_profiles_intro',
            'planned_tests_intro': 'planned_tests_intro',
            'planned_tests_note': 'planned_tests_note',
            'use_scenarios_intro': 'use_scenarios_intro',
            'performance_requirements': 'performance_requirements',
            'completion_conditions': 'completion_conditions',
            'goals_business': 'goals_business',
            'goals_technical': 'goals_technical',
            'tasks_nt': 'tasks_nt',
            'limitations_list': 'limitations_list',
            'customer_requirements_list': 'customer_requirements_list',
            'customer_requirements_note_list': 'customer_requirements_note_list',
            // Таблицы
            'history_changes_table': 'history_changes_table',
            'approval_list_table': 'approval_list_table',
            'abbreviations_table': 'abbreviations_table',
            'terminology_table': 'terminology_table',
            'risks_table': 'risks_table',
            'stand_comparison_table': 'stand_comparison_table',
            'planned_tests_table': 'planned_tests_table',
            'database_preparation_table': 'database_preparation_table',
            'load_profiles_table': 'load_profiles_table',
            'use_scenarios_table': 'use_scenarios_table',
            'monitoring_tools_table': 'monitoring_tools_table',
            'system_resources_table': 'system_resources_table',
            'business_metrics_table': 'business_metrics_table',
            'deliverables_table': 'deliverables_table',
            'contacts_table': 'contacts_table'
        };
        
        // Подсвечиваем измененные поля
        unpublishedChanges.forEach(function(change) {
            const fieldName = change.field;
            const mappedName = fieldMapping[fieldName] || fieldName;
            
            const logMsg = `Обрабатываю поле: ${fieldName} -> ${mappedName}`;
            console.log('[highlight-changes]', logMsg);
            logToServer('DEBUG', logMsg, { field: fieldName, mapped: mappedName });
            
            // Ищем элемент формы
            let element = document.querySelector(`[name="${mappedName}"]`) || 
                         document.getElementById(mappedName) ||
                         document.querySelector(`[name*="${mappedName}"]`);
            
            if (!element) {
                // Для таблиц и списков ищем контейнер
                if (fieldName.includes('_table') || fieldName.includes('_list')) {
                    element = document.querySelector(`[data-field="${fieldName}"]`) ||
                             document.querySelector(`textarea[name="${mappedName}"]`) ||
                             document.querySelector(`div[id*="${mappedName}"]`);
                }
                if (!element) {
                    const warnMsg = `Не найден элемент для поля: ${fieldName} (mapped: ${mappedName})`;
                    console.warn('[highlight-changes]', warnMsg);
                    logToServer('WARNING', warnMsg, { field: fieldName, mapped: mappedName });
                    return; // Пропускаем, если не нашли элемент
                }
            }
            
            const foundMsg = `Найден элемент для ${fieldName}: ${element.tagName} (${element.name || element.id || 'no id'})`;
            console.log('[highlight-changes]', foundMsg);
            logToServer('DEBUG', foundMsg, { field: fieldName, tag: element.tagName, id: element.id || '', name: element.name || '' });
            
            // Создаем индикатор изменения
            const indicator = document.createElement('span');
            indicator.className = 'badge bg-warning text-dark ms-2';
            indicator.style.fontSize = '0.75rem';
            indicator.innerHTML = '⚠ Изменено';
            indicator.title = `Это поле было изменено после последней публикации. Было: ${formatOldValue(change.old)}`;
            
            // Добавляем класс для подсветки
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
                element.classList.add('field-changed');
                
                // Добавляем индикатор рядом с label
                const label = document.querySelector(`label[for="${element.id}"]`) || 
                             element.previousElementSibling ||
                             element.closest('.mb-3')?.querySelector('label') ||
                             element.closest('.form-group')?.querySelector('label');
                
                if (label && !label.querySelector('.change-indicator')) {
                    const changeIndicator = indicator.cloneNode(true);
                    changeIndicator.classList.remove('badge', 'bg-warning', 'text-dark', 'ms-2');
                    changeIndicator.classList.add('change-indicator');
                    changeIndicator.innerHTML = '⚠ Изменено';
                    changeIndicator.style.backgroundColor = '#ffc107';
                    changeIndicator.style.color = '#000';
                    label.appendChild(changeIndicator);
                }
                
                // Добавляем tooltip с информацией о старом значении
                const oldValueText = formatOldValue(change.old);
                element.setAttribute('data-bs-toggle', 'tooltip');
                element.setAttribute('data-bs-placement', 'right');
                element.setAttribute('data-bs-html', 'true');
                element.setAttribute('title', `<strong>Это поле было изменено после публикации</strong><br>Было: ${escapeHtml(oldValueText)}`);
                
                // Инициализируем Bootstrap tooltip после загрузки Bootstrap
                setTimeout(function() {
                    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                        new bootstrap.Tooltip(element);
                    }
                }, 100);
                
                // Помечаем родительскую секцию как имеющую изменения
                const formSection = element.closest('.form-section');
                if (formSection) {
                    formSection.classList.add('has-changes');
                    logToServer('DEBUG', `Секция помечена как имеющая изменения: ${formSection.id || 'no id'}`, { field: fieldName });
                }
                
                logToServer('INFO', `Поле подсвечено: ${fieldName}`, { field: fieldName, mapped: mappedName, tag: element.tagName });
            } else {
                // Для других элементов (div, sections)
                element.style.borderLeft = '4px solid #ffc107';
                element.style.paddingLeft = '10px';
                
                // Добавляем индикатор в заголовок секции
                const heading = element.querySelector('h3, h4, label');
                if (heading && !heading.querySelector('.change-indicator')) {
                    const changeIndicator = indicator.cloneNode(true);
                    changeIndicator.classList.remove('badge', 'bg-warning', 'text-dark', 'ms-2');
                    changeIndicator.classList.add('change-indicator');
                    changeIndicator.style.backgroundColor = '#ffc107';
                    changeIndicator.style.color = '#000';
                    heading.appendChild(changeIndicator);
                }
            }
        });
    });
    
    function formatOldValue(value) {
        if (!value) return 'пусто';
        if (typeof value === 'string') {
            return value.length > 50 ? value.substring(0, 50) + '...' : value;
        }
        if (Array.isArray(value)) {
            return `${value.length} элементов`;
        }
        return String(value);
    }
    
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
    }
    
})();
