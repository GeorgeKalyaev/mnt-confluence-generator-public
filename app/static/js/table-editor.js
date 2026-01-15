/**
 * Простой редактор таблиц для полей формы
 * Позволяет создавать таблицы визуально и сохраняет их в формате с разделителем |
 */

class TableEditor {
    constructor(textareaId) {
        this.textarea = document.getElementById(textareaId);
        if (!this.textarea) return;
        
        this.container = this.textarea.parentElement;
        this.tableData = [];
        this.init();
    }
    
    init() {
        // Создаем структуру редактора
        this.createEditorHTML();
        
        // Загружаем данные из textarea если они есть
        this.loadFromTextarea();
        
        // Инициализируем кнопки
        this.setupButtons();
    }
    
    createEditorHTML() {
        // Скрываем textarea (но оставляем в DOM для отправки формы)
        this.textarea.style.display = 'none';
        
        // Создаем контейнер для редактора
        const editorContainer = document.createElement('div');
        editorContainer.className = 'table-editor-container';
        editorContainer.id = `table-editor-${this.textarea.id}`;
        
        // Кнопки управления
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'table-editor-controls mb-2';
        controlsDiv.innerHTML = `
            <button type="button" class="btn btn-sm btn-outline-primary" data-action="add-row">
                <span>+</span> Добавить строку
            </button>
            <button type="button" class="btn btn-sm btn-outline-primary" data-action="add-col">
                <span>+</span> Добавить столбец
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="remove-col">
                <span>-</span> Удалить столбец
            </button>
            <button type="button" class="btn btn-sm btn-outline-danger" data-action="clear">
                Очистить
            </button>
        `;
        
        // Контейнер для таблицы
        const tableContainer = document.createElement('div');
        tableContainer.className = 'table-editor-table-container';
        tableContainer.style.overflowX = 'auto';
        
        const table = document.createElement('table');
        table.className = 'table table-bordered table-editor-table';
        table.id = `editor-table-${this.textarea.id}`;
        tableContainer.appendChild(table);
        
        editorContainer.appendChild(controlsDiv);
        editorContainer.appendChild(tableContainer);
        
        // Вставляем после label
        this.container.insertBefore(editorContainer, this.textarea.nextSibling);
        
        this.editorContainer = editorContainer;
        this.table = table;
        this.controlsDiv = controlsDiv;
    }
    
    setupButtons() {
        const buttons = this.controlsDiv.querySelectorAll('button[data-action]');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.getAttribute('data-action');
                e.preventDefault();
                e.stopPropagation();
                
                switch(action) {
                    case 'add-row':
                        this.addRow();
                        break;
                    case 'add-col':
                        this.addColumn();
                        break;
                    case 'remove-col':
                        this.removeColumn();
                        break;
                    case 'clear':
                        if (confirm('Очистить таблицу?')) {
                            this.clearTable();
                        }
                        break;
                }
            });
        });
    }
    
    loadFromTextarea() {
        const text = this.textarea.value.trim();
        if (!text) {
            // Если текста нет, создаем пустую таблицу 2x2
            this.createEmptyTable(2, 2);
            return;
        }
        
        // Парсим текст в таблицу
        const lines = text.split('\n').filter(line => line.trim());
        if (lines.length === 0) {
            this.createEmptyTable(2, 2);
            return;
        }
        
        this.tableData = [];
        lines.forEach(line => {
            const cols = line.split('|').map(col => col.trim());
            this.tableData.push(cols);
        });
        
        this.renderTable();
    }
    
    createEmptyTable(rows, cols) {
        this.tableData = [];
        for (let i = 0; i < rows; i++) {
            this.tableData.push(new Array(cols).fill(''));
        }
        this.renderTable();
    }
    
    renderTable() {
        this.table.innerHTML = '';
        
        this.tableData.forEach((row, rowIndex) => {
            const tr = document.createElement('tr');
            
            row.forEach((cell, colIndex) => {
                const td = document.createElement('td');
                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control form-control-sm';
                input.value = cell;
                input.addEventListener('input', () => {
                    this.tableData[rowIndex][colIndex] = input.value;
                    this.syncToTextarea();
                });
                td.appendChild(input);
                tr.appendChild(td);
            });
            
            // Кнопка удаления строки
            const deleteTd = document.createElement('td');
            deleteTd.style.width = '40px';
            deleteTd.style.textAlign = 'center';
            if (this.tableData.length > 1) {
                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.className = 'btn btn-sm btn-link text-danger p-0';
                deleteBtn.innerHTML = '×';
                deleteBtn.title = 'Удалить строку';
                deleteBtn.style.fontSize = '1.5rem';
                deleteBtn.style.lineHeight = '1';
                deleteBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.removeRow(rowIndex);
                });
                deleteTd.appendChild(deleteBtn);
            }
            tr.appendChild(deleteTd);
            
            this.table.appendChild(tr);
        });
        
        this.syncToTextarea();
    }
    
    addRow() {
        const cols = this.tableData.length > 0 ? this.tableData[0].length : 2;
        this.tableData.push(new Array(cols).fill(''));
        this.renderTable();
    }
    
    addColumn() {
        this.tableData.forEach(row => {
            row.push('');
        });
        this.renderTable();
    }
    
    removeRow(index) {
        if (this.tableData.length <= 1) {
            alert('Должна остаться хотя бы одна строка');
            return;
        }
        this.tableData.splice(index, 1);
        this.renderTable();
    }
    
    removeColumn() {
        if (this.tableData.length === 0 || this.tableData[0].length <= 1) {
            alert('Должен остаться хотя бы один столбец');
            return;
        }
        // Удаляем последний столбец (не считая столбец с кнопками удаления)
        this.tableData.forEach(row => {
            row.pop();
        });
        this.renderTable();
    }
    
    clearTable() {
        this.tableData = [['', '']];
        this.renderTable();
    }
    
    syncToTextarea() {
        // Преобразуем таблицу в формат с разделителем |
        const lines = this.tableData.map(row => row.join('|'));
        this.textarea.value = lines.join('\n');
    }
}

// Инициализация редакторов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем редакторы для нужных полей
    const tableFields = ['test_stand_architecture', 'stand_comparison'];
    tableFields.forEach(fieldId => {
        const textarea = document.getElementById(fieldId);
        if (textarea) {
            new TableEditor(fieldId);
        }
    });
});
