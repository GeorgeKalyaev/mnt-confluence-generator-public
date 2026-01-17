/**
 * Drag & Drop функциональность для визуальных таблиц МНТ
 * Позволяет перетаскивать строки таблиц для изменения порядка
 */

class TableDragDrop {
    constructor(tableId, tbodyId, updateCallback) {
        this.table = document.getElementById(tableId);
        this.tbody = document.getElementById(tbodyId);
        this.updateCallback = updateCallback; // Функция обновления скрытого поля
        this.draggedElement = null;
        this.init();
    }
    
    init() {
        if (!this.tbody) return;
        
        // Делаем все строки перетаскиваемыми
        this.makeRowsDraggable();
        
        // Обработчики событий для drag & drop
        this.setupEventListeners();
    }
    
    makeRowsDraggable() {
        const rows = this.tbody.querySelectorAll('tr');
        rows.forEach(row => {
            row.draggable = true;
            row.classList.add('draggable-row');
            
            // Добавляем визуальный индикатор возможности перетаскивания
            // Помещаем его в колонку действий (последняя колонка), рядом с кнопкой удаления
            if (!row.querySelector('.drag-handle')) {
                const lastCell = row.lastElementChild;
                
                // Проверяем, что последняя колонка - это колонка действий
                if (lastCell && (
                    lastCell.querySelector('button.remove-') ||
                    lastCell.querySelector('button[class*="remove"]') ||
                    lastCell.textContent.includes('Удалить') ||
                    lastCell.style.textAlign === 'center' ||
                    lastCell.style.textAlign === 'center'
                )) {
                    // Создаем контейнер для иконки перетаскивания и кнопки удаления
                    const dragHandleSpan = document.createElement('span');
                    dragHandleSpan.className = 'drag-handle';
                    dragHandleSpan.style.cssText = 'cursor: move; user-select: none; margin-right: 8px; color: #666; font-size: 1.2em; display: inline-block; vertical-align: middle;';
                    dragHandleSpan.innerHTML = '☰';
                    dragHandleSpan.setAttribute('title', 'Перетащите для изменения порядка');
                    
                    // Вставляем иконку в начало колонки действий
                    if (lastCell.firstChild) {
                        lastCell.insertBefore(dragHandleSpan, lastCell.firstChild);
                    } else {
                        lastCell.appendChild(dragHandleSpan);
                    }
                    
                    // Делаем всю строку перетаскиваемой при клике на handle
                    dragHandleSpan.addEventListener('mousedown', (e) => {
                        e.stopPropagation();
                    });
                } else {
                    // Если не нашли колонку действий, добавляем как плавающую иконку слева от строки
                    const dragHandle = document.createElement('span');
                    dragHandle.className = 'drag-handle drag-handle-floating';
                    dragHandle.style.cssText = `
                        cursor: move;
                        user-select: none;
                        color: #666;
                        font-size: 1.2em;
                        position: absolute;
                        left: -25px;
                        top: 50%;
                        transform: translateY(-50%);
                        display: inline-block;
                        padding: 4px;
                        opacity: 0.5;
                        transition: opacity 0.2s;
                    `;
                    dragHandle.innerHTML = '☰';
                    dragHandle.setAttribute('title', 'Перетащите для изменения порядка');
                    
                    // Делаем первую ячейку строки относительно позиционированной
                    const firstCell = row.firstElementChild;
                    if (firstCell) {
                        firstCell.style.position = 'relative';
                        firstCell.appendChild(dragHandle);
                    }
                    
                    // Показываем handle при наведении на строку
                    row.addEventListener('mouseenter', () => {
                        dragHandle.style.opacity = '1';
                    });
                    row.addEventListener('mouseleave', () => {
                        dragHandle.style.opacity = '0.5';
                    });
                }
            }
        });
    }
    
    setupEventListeners() {
        // Обработчик начала перетаскивания
        this.tbody.addEventListener('dragstart', (e) => {
            if (e.target.tagName === 'TR' || e.target.closest('tr')) {
                this.draggedElement = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
                this.draggedElement.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', this.draggedElement.innerHTML);
                
                // Добавляем класс для всех других строк (для визуальной обратной связи)
                const rows = this.tbody.querySelectorAll('tr');
                rows.forEach(row => {
                    if (row !== this.draggedElement) {
                        row.classList.add('drag-over');
                    }
                });
            }
        });
        
        // Обработчик перетаскивания над элементом
        this.tbody.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            const targetRow = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
            if (targetRow && targetRow !== this.draggedElement && targetRow.parentNode === this.tbody) {
                // Определяем позицию для вставки
                const rows = Array.from(this.tbody.querySelectorAll('tr'));
                const targetIndex = rows.indexOf(targetRow);
                const draggedIndex = rows.indexOf(this.draggedElement);
                
                // Визуально показываем, куда будет вставлена строка
                rows.forEach(row => row.classList.remove('drag-over-top', 'drag-over-bottom'));
                
                if (draggedIndex < targetIndex) {
                    targetRow.classList.add('drag-over-bottom');
                } else {
                    targetRow.classList.add('drag-over-top');
                }
            }
        });
        
        // Обработчик входа в зону перетаскивания
        this.tbody.addEventListener('dragenter', (e) => {
            e.preventDefault();
            if (e.target.tagName === 'TD' || e.target.tagName === 'TR') {
                const row = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
                if (row && row !== this.draggedElement) {
                    row.classList.add('drag-enter');
                }
            }
        });
        
        // Обработчик выхода из зоны перетаскивания
        this.tbody.addEventListener('dragleave', (e) => {
            const row = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
            if (row) {
                row.classList.remove('drag-enter', 'drag-over-top', 'drag-over-bottom');
            }
        });
        
        // Обработчик завершения перетаскивания
        this.tbody.addEventListener('drop', (e) => {
            e.preventDefault();
            
            const targetRow = e.target.tagName === 'TR' ? e.target : e.target.closest('tr');
            if (targetRow && this.draggedElement && targetRow !== this.draggedElement && targetRow.parentNode === this.tbody) {
                const rows = Array.from(this.tbody.querySelectorAll('tr'));
                const targetIndex = rows.indexOf(targetRow);
                const draggedIndex = rows.indexOf(this.draggedElement);
                
                // Перемещаем элемент
                if (draggedIndex < targetIndex) {
                    this.tbody.insertBefore(this.draggedElement, targetRow.nextSibling);
                } else {
                    this.tbody.insertBefore(this.draggedElement, targetRow);
                }
                
                // Обновляем нумерацию если есть
                this.updateRowNumbers();
                
                // Обновляем скрытое поле через callback
                if (this.updateCallback) {
                    this.updateCallback();
                }
            }
            
            // Очищаем визуальные эффекты
            const rows = this.tbody.querySelectorAll('tr');
            rows.forEach(row => {
                row.classList.remove('dragging', 'drag-over', 'drag-enter', 'drag-over-top', 'drag-over-bottom');
            });
            
            this.draggedElement = null;
        });
        
        // Обработчик завершения перетаскивания (даже если не было drop)
        this.tbody.addEventListener('dragend', (e) => {
            const rows = this.tbody.querySelectorAll('tr');
            rows.forEach(row => {
                row.classList.remove('dragging', 'drag-over', 'drag-enter', 'drag-over-top', 'drag-over-bottom');
            });
            this.draggedElement = null;
        });
    }
    
    updateRowNumbers() {
        // Обновляем нумерацию строк (если она есть)
        const rows = this.tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const numberCell = row.querySelector('.row-number, .contact-number-display, .system-resource-number');
            if (numberCell) {
                const number = index + 1;
                numberCell.textContent = number;
                
                // Обновляем скрытое поле с номером если есть
                const numberInput = row.querySelector('input[type="hidden"].row-number-input, .contact-number, .system-resource-number-input');
                if (numberInput) {
                    numberInput.value = number;
                }
            }
        });
    }
    
    // Метод для обновления drag & drop после добавления новых строк
    refresh() {
        this.makeRowsDraggable();
    }
}

// CSS стили для drag & drop (добавить в CSS файл или style блок)
const dragDropStyles = `
<style>
.draggable-row {
    transition: background-color 0.2s;
}

.draggable-row.dragging {
    opacity: 0.5;
    background-color: #f0f0f0;
}

.draggable-row.drag-over {
    background-color: #e3f2fd;
}

.draggable-row.drag-over-top {
    border-top: 2px solid #2196f3;
}

.draggable-row.drag-over-bottom {
    border-bottom: 2px solid #2196f3;
}

.draggable-row.drag-enter {
    background-color: #bbdefb;
}

.drag-handle {
    cursor: move !important;
    user-select: none;
    color: #666;
}

.drag-handle:hover {
    color: #2196f3;
}

.drag-handle:active {
    cursor: grabbing !important;
}
</style>
`;

// Экспорт для использования в других скриптах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableDragDrop;
}

// Делаем доступным глобально для использования в шаблонах
window.TableDragDrop = TableDragDrop;