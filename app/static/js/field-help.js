/**
 * Система подсказок и помощи для полей формы МНТ
 * Предоставляет tooltips, примеры и справку по разделам
 */

// Справочная информация по разделам МНТ
const MNT_FIELD_HELP = {
    'project_name': {
        tooltip: 'Название проекта, для которого создается МНТ',
        example: 'Например: Претрейд, Тестирование, Микросервис',
        help: 'Укажите краткое название проекта или системы, для которой проводится нагрузочное тестирование.'
    },
    'project': {
        tooltip: 'Название проекта, для которого создается МНТ',
        example: 'Например: Претрейд, Тестирование, Микросервис',
        help: 'Укажите краткое название проекта или системы, для которой проводится нагрузочное тестирование.'
    },
    'title': {
        tooltip: 'Полное название документа МНТ',
        example: 'Например: Методика нагрузочного тестирования системы Претрейд',
        help: 'Обычно включает название системы и указывает на тип документа (МНТ).'
    },
    'mnt_title': {
        tooltip: 'Полное название документа МНТ',
        example: 'Например: Методика нагрузочного тестирования системы Претрейд',
        help: 'Обычно включает название системы и указывает на тип документа (МНТ).'
    },
    'author': {
        tooltip: 'ФИО автора документа',
        example: 'Иванов Иван Иванович',
        help: 'Указывается автор методики нагрузочного тестирования.'
    },
    'abbreviations_table': {
        tooltip: 'Таблица сокращений, используемых в документе',
        example: 'НТ - Нагрузочное тестирование, VU - Виртуальный пользователь',
        help: 'Все сокращения, используемые в документе, должны быть расшифрованы в этой таблице. Это улучшает читаемость документа.'
    },
    'terminology_table': {
        tooltip: 'Таблица терминов и определений',
        example: 'Максимальная производительность - наивысшая интенсивность выполнения операций',
        help: 'Здесь даются определения всех технических терминов, используемых в документе.'
    },
    'introduction_text': {
        tooltip: 'Вводная часть документа',
        example: 'В настоящем документе описаны стратегия и принципы нагрузочного тестирования...',
        help: 'Введение содержит общее описание цели документа и его структуры.'
    },
    'goals_business': {
        tooltip: 'Бизнес-цели нагрузочного тестирования',
        example: '• Оценить готовность системы к пиковым нагрузкам\n• Определить предельные возможности системы',
        help: 'Бизнес-цели описывают, какую пользу принесет НТ для бизнеса (готовность к нагрузкам, соответствие SLA и т.д.).'
    },
    'goals_technical': {
        tooltip: 'Технические цели нагрузочного тестирования',
        example: '• Определить максимальную производительность системы\n• Выявить узкие места в архитектуре',
        help: 'Технические цели описывают конкретные технические результаты, которые нужно достичь (производительность, узкие места и т.д.).'
    },
    'tasks_nt': {
        tooltip: 'Список задач, которые необходимо выполнить в рамках НТ',
        example: '1. Разработать методику НТ\n2. Составить профиль нагрузки\n3. Провести тесты',
        help: 'Задачи должны быть конкретными и измеримыми. Обычно включают разработку методики, подготовку стенда, проведение тестов и составление отчета.'
    },
    'limitations_list': {
        tooltip: 'Ограничения, накладываемые на проведение НТ',
        example: 'НТ не предполагает функционального тестирования\nНТ не направлено на выявление дефектов в аппаратной части',
        help: 'Ограничения описывают, что НЕ входит в scope тестирования и какие ограничения есть для корректной интерпретации результатов.'
    },
    'risks_table': {
        tooltip: 'Таблица рисков, связанных с проведением НТ',
        example: 'Риск: Недоступность тестового стенда | Вероятность: Средняя | Влияние: Высокое',
        help: 'Указываются возможные риски и их влияние на успешное завершение НТ.'
    },
    'object_general': {
        tooltip: 'Общее описание объекта тестирования',
        example: 'Объектом НТ является система Претрейд, предназначенная для...',
        help: 'Дается краткое описание тестируемой системы, её назначение и основные компоненты.'
    },
    'performance_requirements': {
        tooltip: 'Требования к производительности системы',
        example: '• Время отклика не более 2 секунд\n• Поддержка 1000 одновременных пользователей',
        help: 'Указываются конкретные требования к производительности, которые будут проверяться в ходе НТ.'
    },
    'load_profiles_table': {
        tooltip: 'Таблица профилей нагрузки с интенсивностью операций',
        example: 'Главная страница | 100 операций/минута',
        help: 'Профиль нагрузки определяет, какие операции будут выполняться и с какой интенсивностью. Интенсивность обычно указывается в процентах или операциях в минуту.'
    },
    'use_scenarios_table': {
        tooltip: 'Таблица сценариев использования системы',
        example: 'Открытие главной → Просмотр каталога → Добавление в корзину | 100%',
        help: 'Сценарии использования описывают последовательность действий пользователя. Интенсивность указывается относительно базового профиля (обычно 100%).'
    },
    'monitoring_tools_table': {
        tooltip: 'Таблица инструментов мониторинга',
        example: 'Grafana | Визуализация метрик | http://grafana.example.com',
        help: 'Указываются инструменты, которые будут использоваться для мониторинга системы во время НТ.'
    },
    'customer_requirements_list': {
        tooltip: 'Требования к заказчику для успешного проведения НТ',
        example: '• Предоставить доступ к тестовому стенду\n• Обеспечить тестовые данные',
        help: 'Перечисляются требования к заказчику, которые должны быть выполнены для успешного проведения НТ.'
    },
    'tags': {
        tooltip: 'Теги для категоризации документа',
        example: 'Претрейд, Тестирование, Команда А',
        help: 'Теги помогают организовать и находить документы. Можно указать команду, проект, тип тестирования и т.д.'
    }
};

// Инициализация подсказок для полей
function initFieldHelp() {
    // Для каждого поля с подсказкой добавляем иконку помощи
    Object.keys(MNT_FIELD_HELP).forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        const helpInfo = MNT_FIELD_HELP[fieldId];
        const label = field.closest('.mb-3')?.querySelector('label') || 
                     field.previousElementSibling ||
                     field.parentElement.querySelector('label');
        
        if (!label) return;
        
        // Добавляем иконку помощи рядом с label
        if (!label.querySelector('.field-help-icon')) {
            const helpIcon = document.createElement('span');
            helpIcon.className = 'field-help-icon';
            helpIcon.innerHTML = '❓';
            helpIcon.style.cssText = 'margin-left: 5px; cursor: help; color: #06b6d4; font-size: 0.9em; vertical-align: middle;';
            helpIcon.setAttribute('title', helpInfo.tooltip);
            helpIcon.setAttribute('data-bs-toggle', 'tooltip');
            helpIcon.setAttribute('data-bs-placement', 'right');
            helpIcon.setAttribute('data-field-id', fieldId);
            
            helpIcon.addEventListener('click', (e) => {
                e.stopPropagation();
                showFieldHelpModal(fieldId, helpInfo);
            });
            
            label.appendChild(helpIcon);
        }
        
        // Добавляем tooltip при наведении на поле
        field.setAttribute('title', helpInfo.tooltip);
        field.setAttribute('data-bs-toggle', 'tooltip');
        field.setAttribute('data-bs-placement', 'right');
    });
    
    // Инициализируем Bootstrap tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Показываем модальное окно со справкой
function showFieldHelpModal(fieldId, helpInfo) {
    // Создаем или находим модальное окно
    let modal = document.getElementById('field-help-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'field-help-modal';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Справка по полю</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h6 class="mb-3">Описание</h6>
                        <p id="help-description"></p>
                        
                        <h6 class="mb-3 mt-4">Пример</h6>
                        <div class="alert alert-info mb-0" id="help-example"></div>
                        
                        <h6 class="mb-3 mt-4">Дополнительная информация</h6>
                        <p id="help-details"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Заполняем содержимое
    document.getElementById('help-description').textContent = helpInfo.tooltip;
    document.getElementById('help-example').innerHTML = helpInfo.example.replace(/\n/g, '<br>');
    document.getElementById('help-details').textContent = helpInfo.help;
    
    // Показываем модальное окно
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFieldHelp);
} else {
    initFieldHelp();
}

// Экспорт для использования в других скриптах
window.initFieldHelp = initFieldHelp;
window.showFieldHelpModal = showFieldHelpModal;
window.MNT_FIELD_HELP = MNT_FIELD_HELP;