// Автосохранение черновиков
(function() {
    let autoSaveInterval = null;
    let lastSavedData = null;
    let isAutoSaving = false;
    const AUTO_SAVE_INTERVAL = 60000; // 60 секунд
    
    function getFormData() {
        const form = document.querySelector('form[action*="/mnt/"]');
        if (!form) return null;
        
        const formData = new FormData(form);
        const data = {};
        
        // Собираем все поля формы
        for (let [key, value] of formData.entries()) {
            if (key !== 'publish') { // Исключаем publish при автосохранении
                data[key] = value;
            }
        }
        
        return data;
    }
    
    function getFormId() {
        const form = document.querySelector('form[action*="/mnt/"]');
        if (!form) return null;
        
        // Пытаемся определить ID МНТ из action формы
        const match = form.action.match(/\/mnt\/(\d+)\/edit/);
        if (match) {
            return match[1];
        }
        return null;
    }
    
    function showAutoSaveIndicator(status) {
        let indicator = document.getElementById('auto-save-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'auto-save-indicator';
            indicator.style.cssText = 'position: fixed; bottom: 20px; right: 20px; padding: 10px 20px; border-radius: 5px; z-index: 1000; font-size: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);';
            
            const form = document.querySelector('form[action*="/mnt/"]');
            if (form) {
                form.parentElement.appendChild(indicator);
            } else {
                document.body.appendChild(indicator);
            }
        }
        
        if (status === 'saving') {
            indicator.textContent = '💾 Сохранение...';
            indicator.style.backgroundColor = '#fff3cd';
            indicator.style.color = '#856404';
            indicator.style.display = 'block';
        } else if (status === 'saved') {
            indicator.textContent = '✓ Автосохранено ' + new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            indicator.style.backgroundColor = '#d1e7dd';
            indicator.style.color = '#0f5132';
            indicator.style.display = 'block';
            
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        } else if (status === 'error') {
            indicator.textContent = '✗ Ошибка автосохранения';
            indicator.style.backgroundColor = '#f8d7da';
            indicator.style.color = '#842029';
            indicator.style.display = 'block';
            
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 5000);
        }
    }
    
    async function autoSave() {
        const formId = getFormId();
        if (!formId) return; // Только для редактирования существующих МНТ
        
        const currentData = getFormData();
        if (!currentData) return;
        
        // Проверяем, изменились ли данные
        const dataString = JSON.stringify(currentData);
        if (dataString === lastSavedData) {
            return; // Данные не изменились
        }
        
        if (isAutoSaving) return; // Уже идет сохранение
        
        isAutoSaving = true;
        showAutoSaveIndicator('saving');
        
        try {
            const form = document.querySelector('form[action*="/mnt/"]');
            const formData = new FormData(form);
            formData.delete('publish'); // Не публикуем при автосохранении
            
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok || response.redirected) {
                lastSavedData = dataString;
                showAutoSaveIndicator('saved');
            } else {
                throw new Error('Ошибка сохранения');
            }
        } catch (error) {
            console.error('Ошибка автосохранения:', error);
            showAutoSaveIndicator('error');
        } finally {
            isAutoSaving = false;
        }
    }
    
    // Запускаем автосохранение только на странице редактирования
    document.addEventListener('DOMContentLoaded', function() {
        const formId = getFormId();
        if (formId) {
            // Сохраняем начальное состояние
            lastSavedData = JSON.stringify(getFormData());
            
            // Запускаем автосохранение
            autoSaveInterval = setInterval(autoSave, AUTO_SAVE_INTERVAL);
            
            // Останавливаем автосохранение при отправке формы
            const form = document.querySelector('form[action*="/mnt/"]');
            if (form) {
                form.addEventListener('submit', function() {
                    if (autoSaveInterval) {
                        clearInterval(autoSaveInterval);
                    }
                });
            }
        }
    });
})();
