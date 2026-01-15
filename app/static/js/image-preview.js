// Улучшение работы с изображениями - превью перед загрузкой
document.addEventListener('DOMContentLoaded', function() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Находим контейнер для превью
            let previewContainer = input.parentElement.querySelector('.image-preview-container');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.className = 'image-preview-container mt-2';
                input.parentElement.appendChild(previewContainer);
            }
            
            // Очищаем предыдущее превью
            previewContainer.innerHTML = '';
            
            // Создаем превью
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.style.maxWidth = '300px';
                img.style.maxHeight = '300px';
                img.style.border = '1px solid #ddd';
                img.style.borderRadius = '5px';
                img.style.padding = '5px';
                
                const fileName = document.createElement('div');
                fileName.className = 'mt-2 text-muted';
                fileName.textContent = `Файл: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
                
                previewContainer.appendChild(img);
                previewContainer.appendChild(fileName);
            };
            
            reader.readAsDataURL(file);
        });
    });
});
