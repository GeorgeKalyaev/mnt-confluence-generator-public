/**
 * Поддержка загрузки изображений из буфера обмена
 */

(function() {
    'use strict';
    
    // Находим поле для загрузки файлов
    const fileInput = document.getElementById('attachments');
    if (!fileInput) {
        return;
    }
    
    // Создаем контейнер для предпросмотра и кнопки вставки
    const container = fileInput.parentElement;
    const previewContainer = document.createElement('div');
    previewContainer.className = 'mt-3';
    previewContainer.id = 'clipboard-preview-container';
    container.appendChild(previewContainer);
    
    // Кнопка для вставки из буфера обмена
    const pasteButton = document.createElement('button');
    pasteButton.type = 'button';
    pasteButton.className = 'btn btn-outline-secondary btn-sm mt-2';
    pasteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-clipboard" viewBox="0 0 16 16" style="vertical-align: text-bottom; margin-right: 4px;"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>Вставить из буфера обмена (Ctrl+V)';
    container.insertBefore(pasteButton, fileInput.nextSibling);
    
    // Хранилище для изображений из буфера обмена
    const clipboardImages = [];
    
    /**
     * Добавление файла в input
     */
    function addFileToInput(file) {
        const dataTransfer = new DataTransfer();
        
        // Добавляем существующие файлы
        for (let i = 0; i < fileInput.files.length; i++) {
            dataTransfer.items.add(fileInput.files[i]);
        }
        
        // Добавляем новый файл
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        // Обновляем предпросмотр
        updatePreview();
    }
    
    /**
     * Обработка вставки из буфера обмена
     */
    async function handlePaste(event) {
        const items = event.clipboardData.items;
        
        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            
            // Проверяем, является ли элемент изображением
            if (item.type.indexOf('image') !== -1) {
                event.preventDefault();
                
                const blob = item.getAsFile();
                const timestamp = Date.now();
                const filename = `screenshot_${timestamp}.png`;
                
                // Создаем File объект из Blob
                const file = new File([blob], filename, { type: blob.type });
                
                // Добавляем файл в input
                addFileToInput(file);
                
                // Показываем уведомление
                showNotification('Изображение добавлено из буфера обмена');
            }
        }
    }
    
    /**
     * Обработка клика по кнопке вставки
     */
    async function handlePasteButtonClick() {
        try {
            // Запрашиваем разрешение на доступ к буферу обмена
            const clipboardItems = await navigator.clipboard.read();
            
            for (const clipboardItem of clipboardItems) {
                for (const type of clipboardItem.types) {
                    if (type.startsWith('image/')) {
                        const blob = await clipboardItem.getType(type);
                        const timestamp = Date.now();
                        const filename = `screenshot_${timestamp}.png`;
                        
                        // Создаем File объект из Blob
                        const file = new File([blob], filename, { type: type });
                        
                        // Добавляем файл в input
                        addFileToInput(file);
                        
                        // Показываем уведомление
                        showNotification('Изображение добавлено из буфера обмена');
                    }
                }
            }
        } catch (err) {
            console.error('Ошибка при чтении из буфера обмена:', err);
            alert('Не удалось прочитать изображение из буфера обмена. Попробуйте использовать Ctrl+V.');
        }
    }
    
    /**
     * Обновление предпросмотра файлов
     */
    function updatePreview() {
        previewContainer.innerHTML = '';
        
        if (fileInput.files.length === 0) {
            return;
        }
        
        const previewTitle = document.createElement('div');
        previewTitle.className = 'mb-2 fw-bold';
        previewTitle.textContent = `Выбрано файлов: ${fileInput.files.length}`;
        previewContainer.appendChild(previewTitle);
        
        const previewList = document.createElement('div');
        previewList.className = 'list-group';
        
        for (let i = 0; i < fileInput.files.length; i++) {
            const file = fileInput.files[i];
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const fileName = document.createElement('span');
            fileName.textContent = file.name;
            listItem.appendChild(fileName);
            
            const fileSize = document.createElement('small');
            fileSize.className = 'text-muted';
            fileSize.textContent = formatFileSize(file.size);
            listItem.appendChild(fileSize);
            
            previewList.appendChild(listItem);
        }
        
        previewContainer.appendChild(previewList);
    }
    
    /**
     * Форматирование размера файла
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
    
    /**
     * Показ уведомления
     */
    function showNotification(message) {
        // Создаем простое уведомление
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show mt-2';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.appendChild(notification);
        
        // Удаляем уведомление через 3 секунды
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Обработчики событий
    pasteButton.addEventListener('click', handlePasteButtonClick);
    document.addEventListener('paste', handlePaste);
    
    // Обновляем предпросмотр при изменении файлов
    fileInput.addEventListener('change', updatePreview);
    
    // Обновляем предпросмотр при загрузке страницы (если есть файлы)
    updatePreview();
})();
