/**
 * Отслеживание несохраненных изменений в форме
 */

(function() {
    'use strict';
    
    let initialFormData = {};
    let hasUnsavedChanges = false;
    let formElement = null;
    
    // Сохраняем начальное состояние формы
    function saveInitialState() {
        if (!formElement) {
            formElement = document.querySelector('form[method="post"]');
        }
        if (formElement) {
            initialFormData = serializeForm(formElement);
            hasUnsavedChanges = false;
            updateIndicator();
        }
    }
    
    // Сериализация формы в объект
    function serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                // Если ключ уже есть, создаем массив
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        // Также учитываем textarea и select
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                if (input.checked) {
                    const key = input.name;
                    if (data[key]) {
                        if (!Array.isArray(data[key])) {
                            data[key] = [data[key]];
                        }
                        if (!data[key].includes(input.value)) {
                            data[key].push(input.value);
                        }
                    } else {
                        data[key] = input.value;
                    }
                }
            } else if (!formData.has(input.name)) {
                data[input.name] = input.value || '';
            }
        });
        
        return JSON.stringify(data);
    }
    
    // Проверка на изменения
    function checkForChanges() {
        if (!formElement) return;
        
        const currentFormData = serializeForm(formElement);
        hasUnsavedChanges = (currentFormData !== initialFormData);
        updateIndicator();
    }
    
    // Обновление индикатора
    function updateIndicator() {
        let indicator = document.getElementById('unsaved-changes-indicator');
        
        if (!indicator) {
            // Ищем контейнер с кнопками (div с кнопками сохранения)
            const submitButtons = document.querySelectorAll('button[type="submit"]');
            let buttonContainer = null;
            
            if (submitButtons.length > 0) {
                // Ищем родительский контейнер (обычно div с классом d-flex)
                buttonContainer = submitButtons[0].closest('div.d-flex') || submitButtons[0].parentNode;
            }
            
            if (!buttonContainer) {
                // Если не нашли, создаем контейнер рядом с кнопками
                const formActions = formElement.querySelector('.form-actions') || 
                                  formElement.querySelector('div:has(button[type="submit"])') ||
                                  formElement;
                buttonContainer = formActions;
            }
            
            // Создаем компактный индикатор как небольшой бейдж
            indicator = document.createElement('span');
            indicator.id = 'unsaved-changes-indicator';
            indicator.className = 'badge bg-warning text-dark align-self-center';
            indicator.style.display = 'none';
            indicator.style.fontSize = '0.75rem';
            indicator.style.padding = '0.35em 0.65em';
            indicator.style.cursor = 'default';
            indicator.style.whiteSpace = 'nowrap';
            indicator.innerHTML = '<span style="font-size: 0.9em;">⚠</span> Несохраненные изменения';
            indicator.title = 'В форме есть несохраненные изменения. Не забудьте сохранить!';
            
            // Вставляем индикатор в контейнер с кнопками (в конец, чтобы был справа)
            if (buttonContainer) {
                // Если контейнер имеет d-flex, добавляем margin-left: auto для выравнивания справа
                const computedStyle = window.getComputedStyle(buttonContainer);
                if (computedStyle.display === 'flex' || buttonContainer.classList.contains('d-flex')) {
                    indicator.style.marginLeft = 'auto';
                }
                buttonContainer.appendChild(indicator);
            } else {
                document.body.appendChild(indicator);
            }
        }
        
        if (hasUnsavedChanges) {
            indicator.style.display = 'inline-block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    // Откат изменений
    function resetForm() {
        if (!formElement || !confirm('Вы уверены, что хотите отменить все несохраненные изменения?')) {
            return;
        }
        
        // Перезагружаем страницу для сброса формы
        window.location.reload();
    }
    
    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        saveInitialState();
        
        // Отслеживание изменений в полях формы
        if (formElement) {
            formElement.addEventListener('input', function(e) {
                // Исключаем поля, которые не должны триггерить изменение (например, скрытые поля)
                if (e.target.type !== 'hidden' && e.target.name !== 'publish_hidden') {
                    checkForChanges();
                }
            });
            
            formElement.addEventListener('change', function(e) {
                if (e.target.type !== 'hidden' && e.target.name !== 'publish_hidden') {
                    checkForChanges();
                }
            });
            
            // При отправке формы сбрасываем флаг
            formElement.addEventListener('submit', function() {
                hasUnsavedChanges = false;
                updateIndicator();
            });
            
            // Предупреждение при уходе со страницы с несохраненными изменениями
            window.addEventListener('beforeunload', function(e) {
                if (hasUnsavedChanges) {
                    e.preventDefault();
                    e.returnValue = 'У вас есть несохраненные изменения. Вы уверены, что хотите покинуть страницу?';
                    return e.returnValue;
                }
            });
        }
        
        // Создаем кнопку отката, если её нет
        const resetButton = document.getElementById('reset-changes-btn');
        if (!resetButton) {
            const formActions = document.querySelector('.form-actions') || 
                              document.querySelector('form[method="post"]') ||
                              document.body;
            
            const button = document.createElement('button');
            button.type = 'button';
            button.id = 'reset-changes-btn';
            button.className = 'btn btn-outline-warning me-2';
            button.innerHTML = '↺ Отменить изменения';
            button.style.display = 'none';
            button.onclick = resetForm;
            
            // Ищем место для вставки (перед кнопками сохранения)
            const submitButtons = document.querySelectorAll('button[type="submit"]');
            if (submitButtons.length > 0) {
                submitButtons[0].parentNode.insertBefore(button, submitButtons[0]);
            } else {
                formActions.appendChild(button);
            }
            
            // Показываем/скрываем кнопку в зависимости от изменений
            const observer = new MutationObserver(function() {
                if (document.getElementById('reset-changes-btn')) {
                    document.getElementById('reset-changes-btn').style.display = hasUnsavedChanges ? 'inline-block' : 'none';
                }
            });
            
            // Обновляем отображение кнопки при изменении флага
            const checkButton = setInterval(function() {
                const btn = document.getElementById('reset-changes-btn');
                if (btn) {
                    btn.style.display = hasUnsavedChanges ? 'inline-block' : 'none';
                }
                if (!hasUnsavedChanges && btn && btn.style.display === 'none') {
                    clearInterval(checkButton);
                }
            }, 500);
        }
    });
    
    // Экспортируем функции для использования извне
    window.unsavedChangesTracker = {
        checkForChanges: checkForChanges,
        resetForm: resetForm,
        hasUnsavedChanges: function() { return hasUnsavedChanges; }
    };
    
})();
