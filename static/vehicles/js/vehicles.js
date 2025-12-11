/**
 * EnhancedVehicleAnalyzer - Улучшенный анализатор данных ТС
 */
class EnhancedVehicleAnalyzer {
    constructor() {
        this.vehicles = [];
        this.selectedVehicles = [];
        this.rawData = null;
        this.chart = null;
        this.playerInterval = null;
        this.isPlaying = false;
        this.currentTimeIndex = 0;
        this.playerSpeed = 1;
        this.timeData = [];
        this.selectedParams = [];
        this.activeCharts = [];
        this.multiCharts = [];
        this.zoomLevel = 100;
        this.chartOffset = 0;
        this.showAllData = true;
        this.paramColors = new Map();

        // Отладка
        this.debugMode = true;
        this.log = (...args) => {
            if (this.debugMode) {
                console.log('[ENHANCED ANALYZER]', ...args);
            }
        };

        // Полный словарь перевода параметров
        this.paramTranslations = {
            // Скорость и движение
            'Speed': 'Текущая скорость',
            'MaxSpeed': 'Максимальная скорость',
            'AverageSpeed': 'Средняя скорость',
            'SpeedLimit': 'Ограничение скорости',
            'OverspeedCount': 'Превышения скорости',
            'TotalDistance': 'Общий пробег',
            'MoveDuration': 'Время движения',
            'ParkDuration': 'Время стоянки',
            'ParkCount': 'Количество остановок',

            // Топливо
            'Engine1FuelConsum': 'Расход топлива',
            'TankMainFuelLevel': 'Уровень топлива',
            'TankMainFuelLevel First': 'Начальный уровень топлива',
            'TankMainFuelLevel Last': 'Конечный уровень топлива',
            'TankMainFuelUpVol Diff': 'Заправка топлива',
            'TankMainFuelDnVol Diff': 'Слив топлива',
            'Engine1FuelConsumMPer100km': 'Расход на 100 км',
            'Engine1FuelConsumP/M': 'Расход топлива (л/ч)',
            'Engine1FuelConsumDuringMH': 'Расход за моточасы',
            'Engine1FuelConsumP/MDuringMH': 'Удельный расход',

            // Двигатель
            'Engine1Motohours': 'Моточасы',
            'Engine1MHOnParks': 'Моточасы на стоянках',
            'Engine1MHInMove': 'Моточасы в движении',
            'EngineRPM': 'Обороты двигателя',
            'EngineTemperature': 'Температура двигателя',
            'EngineOilPressure': 'Давление масла',

            // Качество вождения
            'DQRating': 'Рейтинг вождения',
            'DQOverspeedPoints Diff': 'Очки превышения скорости',
            'DQExcessAccelPoints Diff': 'Очки резкого ускорения',
            'DQExcessBrakePoints Diff': 'Очки резкого торможения',
            'DQEmergencyBrakePoints Diff': 'Очки экстренного торможения',
            'DQExcessRightPoints Diff': 'Очки резкого поворота вправо',
            'DQExcessLeftPoints Diff': 'Очки резкого поворота влево',
            'DQExcessBumpPoints Diff': 'Очки ударов',
            'DQPoints Diff': 'Общие очки качества',

            // Время и работа
            'TotalDuration': 'Общее время',
            'WorkTime': 'Время работы',
            'IdleTime': 'Время простоя',
            'Duration': 'Длительность',

            // Координаты и GPS
            'Longitude': 'Долгота',
            'Latitude': 'Широта',
            'Altitude': 'Высота',
            'Course': 'Курс',
            'GPSSatellites': 'Спутники GPS',
            'GPSHDOP': 'Точность GPS',

            // Сигнал и питание
            'GSMLevel': 'Уровень сигнала GSM',
            'PowerVoltage': 'Напряжение питания',
            'InternalTemperature': 'Внутренняя температура',

            // CAN-данные
            'CAN_Speed': 'CAN Скорость',
            'CAN_RPM': 'CAN Обороты',
            'CAN_FuelLevel': 'CAN Уровень топлива',
            'CAN_OilPressure': 'CAN Давление масла',
            'CAN_Temperature': 'CAN Температура',

            // Датчики
            'Temperature1': 'Температура 1',
            'Temperature2': 'Температура 2',
            'Temperature3': 'Температура 3',
            'Pressure1': 'Давление 1',
            'Pressure2': 'Давление 2',
            'AnalogInput1': 'Аналоговый вход 1',
            'AnalogInput2': 'Аналоговый вход 2',
            'AnalogInput3': 'Аналоговый вход 3',
            'AnalogInput4': 'Аналоговый вход 4'
        };

        // Предустановленные цветовые схемы
        this.colorSchemes = {
            speed: ['#FF6B6B', '#FFD166', '#06D6A0', '#118AB2'],
            fuel: ['#EF476F', '#FFD166', '#06D6A0', '#073B4C'],
            safety: ['#9D4EDD', '#7209B7', '#560BAD', '#3A0CA3'],
            engine: ['#FF9E00', '#FF9100', '#FF8500', '#FF6D00'],
            default: ['#FFD700', '#FFA500', '#FF8C00', '#FF7F50']
        };

        // Шаблоны отчетов
        this.presets = {
            fuel: {
                name: 'Расход топлива',
                params: ['Engine1FuelConsum', 'TankMainFuelLevel', 'Engine1FuelConsumMPer100km', 'TotalDistance'],
                colors: this.colorSchemes.fuel
            },
            mileage: {
                name: 'Пробег и движение',
                params: ['TotalDistance', 'AverageSpeed', 'MaxSpeed', 'MoveDuration', 'ParkDuration'],
                colors: this.colorSchemes.speed
            },
            safety: {
                name: 'Безопасность',
                params: ['DQRating', 'OverspeedCount', 'MaxSpeed', 'DQExcessBrakePoints Diff', 'DQExcessAccelPoints Diff'],
                colors: this.colorSchemes.safety
            },
            engine: {
                name: 'Двигатель',
                params: ['Engine1Motohours', 'EngineRPM', 'EngineTemperature', 'EngineOilPressure'],
                colors: this.colorSchemes.engine
            },
            all: {
                name: 'Все показатели',
                params: ['TotalDistance', 'Engine1FuelConsum', 'DQRating', 'Engine1Motohours', 'AverageSpeed', 'MoveDuration'],
                colors: this.colorSchemes.default
            }
        };

        // Стандартные цвета для параметров
        this.defaultColors = [
            '#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2',
            '#9D4EDD', '#EF476F', '#FF9E00', '#7209B7', '#560BAD',
            '#3A0CA3', '#4361EE', '#3A86FF', '#FB5607', '#8338EC',
            '#FF006E', '#FFBE0B', '#FB5607', '#8338EC', '#3A86FF'
        ];
    }

    // ============================================
    // ИНИЦИАЛИЗАЦИЯ
    // ============================================
    async init() {
        this.log('🚀 Инициализация улучшенного анализатора ТС');
        try {
            await this.loadVehicles();
            this.setupEventListeners();
            this.setupPlayer();
            this.setupChartControls();
            this.setupTabSwitching();
            this.setupColorPicker();
            this.showNotification('Система анализа данных ТС готова к работе', 'info');
        } catch (error) {
            console.error('Ошибка инициализации:', error);
            this.showNotification('Ошибка инициализации: ' + error.message, 'error');
        }
    }

    async loadVehicles() {
        this.showLoading('Загрузка ТС', 'Получение списка транспортных средств...');
        try {
            const response = await fetch('/vehicles/api/get-vehicles/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) throw new Error(`HTTP ошибка ${response.status}`);

            const data = await response.json();
            if (data.success) {
                this.vehicles = data.data.vehicles || [];
                this.log(`✅ Загружено ТС: ${this.vehicles.length}`);
                this.renderVehiclesList();
            } else {
                throw new Error(data.error || 'Ошибка загрузки ТС');
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки ТС:', error);
            this.showNotification('Ошибка загрузки ТС: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadData() {
        if (this.selectedVehicles.length === 0) {
            this.showNotification('Выберите хотя бы одно ТС', 'warning');
            return;
        }

        const startDate = document.getElementById('dateFrom')?.value;
        const endDate = document.getElementById('dateTo')?.value;

        if (!startDate || !endDate) {
            this.showNotification('Укажите период анализа', 'warning');
            return;
        }

        if (new Date(startDate) > new Date(endDate)) {
            this.showNotification('Дата начала не может быть позже даты окончания', 'error');
            return;
        }

        try {
            this.showLoading('Загрузка данных', 'Получение исторических данных...');
            this.updateProgress(20, 'Подготовка запроса...');

            const response = await fetch('/vehicles/api/get-all-historical-data/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    vehicle_ids: this.selectedVehicles,
                    start_date: startDate,
                    end_date: endDate,
                    all_params: true
                })
            });

            this.updateProgress(40, 'Получение ответа...');

            if (!response.ok) {
                throw new Error(`HTTP ошибка ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Ошибка загрузки данных');
            }

            if (!data.data || !data.data.historical_data) {
                throw new Error('Нет данных в ответе');
            }

            this.rawData = data.data.historical_data;
            this.updateProgress(60, 'Обработка данных...');

            this.processTimeSeriesData();

            if (this.timeData.length === 0) {
                this.showNotification('Нет данных для выбранного периода', 'warning');
                this.hideLoading();
                return;
            }

            this.updateProgress(80, 'Обновление интерфейса...');

            this.updateStatistics(data.data);
            this.renderDataTable();
            this.populateChartParams();
            this.showInterfaceSections();
            this.showTableTab();

            // Автоматически применяем первый шаблон
            if (this.timeData.length > 0) {
                this.applyPreset('fuel');
            }

            this.showNotification(`Данные успешно загружены: ${this.timeData.length} записей`, 'success');

        } catch (error) {
            console.error('❌ Ошибка загрузки данных:', error);
            this.showNotification('Ошибка загрузки: ' + error.message, 'error');
        } finally {
            this.updateProgress(100, 'Завершено');
            setTimeout(() => this.hideLoading(), 1000);
        }
    }

    // ============================================
    // ОТОБРАЖЕНИЕ ДАННЫХ
    // ============================================
    processTimeSeriesData() {
        this.log('Начинаем обработку time series данных');

        if (!this.rawData) {
            this.timeData = [];
            return;
        }

        this.timeData = this.rawData.time_series || [];

        if (this.timeData.length > 0) {
            // Сортируем по времени
            this.timeData.sort((a, b) => {
                const timeA = a.timestamp || a.date || a.dt || a.start_time || '';
                const timeB = b.timestamp || b.date || b.dt || b.start_time || '';
                return new Date(timeA) - new Date(timeB);
            });
        }

        this.updatePlayerData();
        this.log(`Обработано временных данных: ${this.timeData.length}`);
    }

    renderDataTable() {
        const container = document.getElementById('dataTableBody');
        if (!container) {
            this.log('❌ Контейнер таблицы не найден');
            return;
        }

        if (this.timeData.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center py-4">
                        <i class="fas fa-database fa-2x text-muted mb-3"></i>
                        <p class="text-muted mb-0">Нет данных</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.log(`Рендерим таблицу с ${this.timeData.length} записями`);

        let html = '';
        const displayData = this.showAllData ? this.timeData : this.timeData.slice(0, 100);

        displayData.forEach((item, index) => {
            const getValue = (key) => {
                if (item.values && item.values[key] !== undefined) {
                    const val = item.values[key];
                    if (typeof val === 'string' && val.includes(':')) {
                        return this.formatTimeToHours(val);
                    }
                    return typeof val === 'number' ? val.toFixed(2) : val || '0.00';
                }
                return '0.00';
            };

            const vehicleName = item.vehicle_name || item.vehicle || '—';
            const timestamp = item.timestamp || item.date || item.dt || item.start_time || '—';

            html += `
                <tr onclick="analyzer.selectTableRow(${index})" style="cursor: pointer;">
                    <td>${vehicleName}</td>
                    <td>${this.formatDateTime(timestamp)}</td>
                    <td class="text-end">${getValue('TotalDistance')}</td>
                    <td class="text-end">${getValue('AverageSpeed')}</td>
                    <td class="text-end">${getValue('Engine1FuelConsum')}</td>
                    <td class="text-end">${getValue('DQRating')}</td>
                    <td class="text-end">${getValue('Engine1Motohours')}</td>
                    <td class="text-end">${getValue('MoveDuration')}</td>
                    <td class="text-end">${getValue('ParkDuration')}</td>
                </tr>
            `;
        });

        if (!this.showAllData && this.timeData.length > 100) {
            html += `
                <tr style="background: rgba(255,215,0,0.1);">
                    <td colspan="9" class="text-center">
                        <i class="fas fa-info-circle"></i>
                        Показано 100 из ${this.timeData.length} записей
                        <button onclick="analyzer.toggleShowAll()" class="btn btn-sm btn-outline-gold ms-3">
                            Показать все
                        </button>
                    </td>
                </tr>
            `;
        }

        container.innerHTML = html;
        this.log('✅ Таблица отрендерена');
    }

    toggleShowAll() {
        const switchElement = document.getElementById('showAllDataSwitch');
        this.showAllData = !this.showAllData;

        if (switchElement) {
            switchElement.checked = this.showAllData;
        }

        this.renderDataTable();
        this.showNotification(
            this.showAllData
                ? `Показаны все ${this.timeData.length} записей`
                : 'Показано 100 записей',
            'info'
        );
    }

    // ============================================
    // ГРАФИКИ
    // ============================================
    addChart() {
        const paramSelect = document.getElementById('chartParamSelect');
        const colorSelect = document.getElementById('chartColorSelect');
        const chartType = document.getElementById('chartTypeSelect').value;

        if (!paramSelect.value) {
            this.showNotification('Выберите параметр для графика', 'warning');
            return;
        }

        const param = paramSelect.value;
        const color = colorSelect.value;
        const translatedParam = this.translateParam(param);

        // Сохраняем цвет для параметра
        this.paramColors.set(param, color);

        // Добавляем в активные графики
        if (!this.activeCharts.some(chart => chart.param === param)) {
            this.activeCharts.push({
                param: param,
                name: translatedParam,
                color: color,
                type: chartType
            });

            this.updateActiveChartsDisplay();
            this.createCombinedChart();
        } else {
            this.showNotification('Этот параметр уже добавлен в график', 'info');
        }
    }

    removeChart(param) {
        const index = this.activeCharts.findIndex(chart => chart.param === param);
        if (index > -1) {
            this.activeCharts.splice(index, 1);
            this.updateActiveChartsDisplay();
            this.createCombinedChart();
        }
    }

    updateActiveChartsDisplay() {
        const container = document.getElementById('activeCharts');
        if (!container) return;

        if (this.activeCharts.length === 0) {
            container.innerHTML = '<div class="text-muted">Нет активных графиков</div>';
            return;
        }

        let html = '';
        this.activeCharts.forEach((chart, index) => {
            html += `
                <div class="chart-badge">
                    <div class="chart-badge-color" style="background-color: ${chart.color}"></div>
                    <span>${chart.name}</span>
                    <button class="chart-badge-close" onclick="analyzer.removeChart('${chart.param}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    createCombinedChart() {
        if (this.timeData.length === 0 || this.activeCharts.length === 0) {
            return;
        }

        const chartData = this.prepareCombinedChartData();

        if (!chartData || chartData.labels.length === 0) {
            this.showNotification('Нет данных для выбранных параметров', 'warning');
            return;
        }

        this.renderCombinedChart(chartData);
        this.updateChartControls();
    }

    prepareCombinedChartData() {
        if (this.timeData.length === 0) return null;

        const datasets = [];
        const labels = this.timeData.map(item => {
            const timestamp = item.timestamp || item.date || item.dt || item.start_time || '';
            return new Date(timestamp);
        });

        this.activeCharts.forEach((chart, index) => {
            const paramData = [];

            this.timeData.forEach(item => {
                let value = 0;
                if (item.values && item.values[chart.param] !== undefined) {
                    const val = item.values[chart.param];
                    if (typeof val === 'string' && val.includes(':')) {
                        value = this.formatTimeToHours(val);
                    } else {
                        value = this.getNumericValue(val);
                    }
                }
                paramData.push(value);
            });

            datasets.push({
                label: chart.name,
                data: paramData,
                borderColor: chart.color,
                backgroundColor: chart.color + '40',
                borderWidth: 2,
                fill: false,
                tension: 0.3,
                pointRadius: 2,
                yAxisID: `y${index}`
            });
        });

        return { labels, datasets };
    }

    renderCombinedChart(data) {
        const canvas = document.getElementById('mainChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        if (this.chart) {
            this.chart.destroy();
        }

        // Создаем оси для каждого графика
        const scales = {
            x: {
                type: 'time',
                time: {
                    unit: 'day',
                    displayFormats: {
                        day: 'dd.MM.yyyy'
                    }
                },
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: '#CCCCCC' },
                title: {
                    display: true,
                    text: 'Дата и время',
                    color: '#CCCCCC'
                }
            }
        };

        // Добавляем оси Y для каждого графика
        data.datasets.forEach((dataset, index) => {
            scales[`y${index}`] = {
                type: 'linear',
                display: true,
                position: index === 0 ? 'left' : 'right',
                grid: {
                    drawOnChartArea: index === 0,
                    color: 'rgba(255,255,255,0.1)'
                },
                ticks: { color: dataset.borderColor },
                title: {
                    display: true,
                    text: dataset.label,
                    color: dataset.borderColor
                }
            };
        });

        this.chart = new Chart(ctx, {
            type: this.activeCharts[0].type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#FFFFFF',
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#FFD700',
                        bodyColor: '#FFFFFF',
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value.toFixed(2)}`;
                            },
                            title: (context) => {
                                const date = new Date(context[0].parsed.x);
                                return date.toLocaleString('ru-RU');
                            }
                        }
                    }
                },
                scales: scales
            }
        });

        this.updateChartRangeInfo();
    }

    // ============================================
    // МУЛЬТИГРАФИКИ
    // ============================================
    addMultiChart() {
        const chartId = 'chart_' + Date.now();

        const chartContainer = document.getElementById('multiChartsContainer');
        const emptyState = chartContainer.querySelector('.text-center');

        if (emptyState) {
            emptyState.remove();
        }

        const chartHtml = `
            <div class="multi-chart-item" id="${chartId}">
                <div class="multi-chart-header">
                    <h6 class="multi-chart-title">Новый график</h6>
                    <div class="multi-chart-controls">
                        <button class="btn btn-sm btn-outline-gold" onclick="analyzer.configureChart('${chartId}')">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="analyzer.removeMultiChart('${chartId}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="multi-chart-body">
                    <canvas id="${chartId}_canvas"></canvas>
                </div>
            </div>
        `;

        chartContainer.insertAdjacentHTML('beforeend', chartHtml);

        // Сохраняем информацию о графике
        this.multiCharts.push({
            id: chartId,
            params: [],
            colors: [],
            type: 'line'
        });
    }

    configureChart(chartId) {
        // Реализация настройки графика
        this.showNotification('Настройка графика будет доступна в следующей версии', 'info');
    }

    removeMultiChart(chartId) {
        const chartElement = document.getElementById(chartId);
        if (chartElement) {
            chartElement.remove();
        }

        const index = this.multiCharts.findIndex(chart => chart.id === chartId);
        if (index > -1) {
            this.multiCharts.splice(index, 1);
        }

        // Если графиков не осталось, показываем пустое состояние
        const chartContainer = document.getElementById('multiChartsContainer');
        if (chartContainer.children.length === 0) {
            chartContainer.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-chart-area fa-3x text-muted mb-3"></i>
                    <h5 class="text-gold mb-2">Нет активных графиков</h5>
                    <p class="text-muted mb-0">Добавьте первый график с помощью кнопки "Новый график"</p>
                </div>
            `;
        }
    }

    clearAllCharts() {
        const chartContainer = document.getElementById('multiChartsContainer');
        chartContainer.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-chart-area fa-3x text-muted mb-3"></i>
                <h5 class="text-gold mb-2">Нет активных графиков</h5>
                <p class="text-muted mb-0">Добавьте первый график с помощью кнопки "Новый график"</p>
            </div>
        `;

        this.multiCharts = [];
        this.showNotification('Все графики удалены', 'info');
    }

    // ============================================
    // ШАБЛОНЫ И НАСТРОЙКИ
    // ============================================
    applyPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (!preset) {
            this.showNotification('Шаблон не найден', 'error');
            return;
        }

        // Очищаем активные графики
        this.activeCharts = [];

        // Добавляем параметры из шаблона
        preset.params.forEach((param, index) => {
            const color = preset.colors[index] || this.getDefaultColor(index);

            this.activeCharts.push({
                param: param,
                name: this.translateParam(param),
                color: color,
                type: 'line'
            });

            // Сохраняем цвет
            this.paramColors.set(param, color);
        });

        // Обновляем интерфейс
        this.updateActiveChartsDisplay();
        this.createCombinedChart();

        // Переключаемся на вкладку графиков
        this.switchTab('charts');

        this.showNotification(`Применен шаблон: ${preset.name}`, 'success');
    }

    showPresets() {
        this.showNotification('Используйте кнопки шаблонов для быстрого создания отчетов', 'info');
    }

    // ============================================
    // ЦВЕТА И НАСТРОЙКИ
    // ============================================
    setupColorPicker() {
        const colorGrid = document.getElementById('colorPickerGrid');
        if (!colorGrid) return;

        let html = '';
        this.defaultColors.forEach((color, index) => {
            html += `
                <div class="color-item" 
                     style="background-color: ${color}"
                     onclick="analyzer.selectColor('${color}')"
                     data-color="${color}"></div>
            `;
        });

        colorGrid.innerHTML = html;
    }

    selectColor(color) {
        // Убираем выделение со всех цветов
        document.querySelectorAll('.color-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Выделяем выбранный цвет
        const selectedItem = document.querySelector(`.color-item[data-color="${color}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }

        // Устанавливаем цвет в поле выбора
        const colorSelect = document.getElementById('chartColorSelect');
        if (colorSelect) {
            colorSelect.value = color;
        }
    }

    applySelectedColor() {
        const colorSelect = document.getElementById('chartColorSelect');
        if (colorSelect) {
            this.selectColor(colorSelect.value);
        }

        // Закрываем модальное окно
        const modal = bootstrap.Modal.getInstance(document.getElementById('colorPickerModal'));
        if (modal) {
            modal.hide();
        }
    }

    getDefaultColor(index) {
        return this.defaultColors[index % this.defaultColors.length];
    }

    // ============================================
    // ИНТЕРФЕЙС
    // ============================================
    showInterfaceSections() {
        const sections = ['playerSection', 'chartsSection'];
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                section.classList.remove('d-none');
                this.log(`Секция показана: ${id}`);
            }
        });
    }

    switchTab(tabName) {
        // Убираем активный класс у всех кнопок
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Скрываем все вкладки
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });

        // Активируем выбранную кнопку
        const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }

        // Показываем выбранную вкладку
        const activeTab = document.getElementById(`${tabName}Tab`);
        if (activeTab) {
            activeTab.classList.add('active');
            activeTab.style.display = 'block';
        }

        // Если переключились на графики и есть данные - обновляем график
        if (tabName === 'charts' && this.timeData.length > 0 && this.activeCharts.length > 0) {
            this.createCombinedChart();
        }

        this.log(`✅ Вкладка ${tabName} активирована`);
    }

    showTableTab() {
        this.switchTab('table');
    }

    // ============================================
    // ПОЛЕЗНЫЕ ФУНКЦИИ
    // ============================================
    populateChartParams() {
        const select = document.getElementById('chartParamSelect');
        if (!select) return;

        const allParams = new Set();

        // Собираем все параметры из данных
        if (this.rawData.parameters && Array.isArray(this.rawData.parameters)) {
            this.rawData.parameters.forEach(param => allParams.add(param));
        }

        this.timeData.forEach(item => {
            if (item.values && typeof item.values === 'object') {
                Object.keys(item.values).forEach(param => allParams.add(param));
            }
        });

        // Сортируем параметры
        const sortedParams = Array.from(allParams).sort((a, b) => {
            const transA = this.translateParam(a).toLowerCase();
            const transB = this.translateParam(b).toLowerCase();
            return transA.localeCompare(transB);
        });

        // Заполняем селект
        let html = '<option value="">Выберите параметр...</option>';

        sortedParams.forEach(param => {
            const translated = this.translateParam(param);
            html += `<option value="${param}">${translated}</option>`;
        });

        select.innerHTML = html;
    }

    translateParam(param) {
        return this.paramTranslations[param] || param;
    }

    getNumericValue(value) {
        if (value === undefined || value === null || value === '') {
            return 0;
        }

        if (typeof value === 'number') {
            return value;
        }

        if (typeof value === 'string') {
            // Пытаемся преобразовать строку в число
            const num = parseFloat(value.replace(',', '.'));
            if (!isNaN(num)) {
                return num;
            }

            // Если это время в формате HH:MM:SS
            if (value.includes(':')) {
                return this.formatTimeToHours(value);
            }
        }

        return 0;
    }

    // ============================================
    // ПЛЕЕР ДАННЫХ
    // ============================================
    setupPlayer() {
        const playerPlayBtn = document.getElementById('playerPlay');
        const playerPauseBtn = document.getElementById('playerPause');
        const playerStopBtn = document.getElementById('playerStop');
        const playerPrevBtn = document.getElementById('playerPrev');
        const playerNextBtn = document.getElementById('playerNext');
        const timeline = document.getElementById('playerTimeline');
        const speedSelect = document.getElementById('playerSpeed');

        if (playerPlayBtn) playerPlayBtn.addEventListener('click', () => this.togglePlay());
        if (playerPauseBtn) playerPauseBtn.addEventListener('click', () => this.pause());
        if (playerStopBtn) playerStopBtn.addEventListener('click', () => this.stop());
        if (playerPrevBtn) playerPrevBtn.addEventListener('click', () => this.prev());
        if (playerNextBtn) playerNextBtn.addEventListener('click', () => this.next());

        if (timeline) {
            timeline.addEventListener('click', (e) => {
                const rect = timeline.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                this.seekTo(percent);
            });
        }

        if (speedSelect) {
            speedSelect.addEventListener('change', (e) => {
                this.playerSpeed = parseFloat(e.target.value);
                if (this.isPlaying) this.startPlayback();
            });
        }
    }

    updatePlayerData() {
        if (this.timeData.length === 0) {
            this.currentTimeIndex = 0;
            this.updatePlayerDisplay();
            return;
        }

        this.updatePlayerDisplay();
    }

    togglePlay() {
        if (this.timeData.length === 0) {
            this.showNotification('Нет данных для воспроизведения', 'warning');
            return;
        }

        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (this.timeData.length === 0) return;

        this.isPlaying = true;
        const playerPlayBtn = document.getElementById('playerPlay');

        if (playerPlayBtn) {
            playerPlayBtn.innerHTML = '<i class="fas fa-pause"></i>';
            playerPlayBtn.title = 'Пауза';
        }

        this.startPlayback();
    }

    pause() {
        this.isPlaying = false;
        const playerPlayBtn = document.getElementById('playerPlay');

        if (playerPlayBtn) {
            playerPlayBtn.innerHTML = '<i class="fas fa-play"></i>';
            playerPlayBtn.title = 'Воспроизвести';
        }

        this.stopPlayback();
    }

    stop() {
        this.pause();
        this.currentTimeIndex = 0;
        this.updatePlayerDisplay();
    }

    prev() {
        if (this.timeData.length === 0) return;

        this.currentTimeIndex = Math.max(0, this.currentTimeIndex - 1);
        this.updatePlayerDisplay();
    }

    next() {
        if (this.timeData.length === 0) return;

        this.currentTimeIndex = Math.min(this.timeData.length - 1, this.currentTimeIndex + 1);
        this.updatePlayerDisplay();
    }

    seekTo(percent) {
        if (this.timeData.length === 0) return;

        this.currentTimeIndex = Math.floor(percent * (this.timeData.length - 1));
        this.updatePlayerDisplay();
    }

    startPlayback() {
        this.stopPlayback();

        this.playerInterval = setInterval(() => {
            this.currentTimeIndex = (this.currentTimeIndex + 1) % this.timeData.length;
            this.updatePlayerDisplay();

            if (this.currentTimeIndex === this.timeData.length - 1) {
                this.pause();
            }
        }, 1000 / this.playerSpeed);
    }

    stopPlayback() {
        if (this.playerInterval) {
            clearInterval(this.playerInterval);
            this.playerInterval = null;
        }
    }

    updatePlayerDisplay() {
        if (this.timeData.length === 0) {
            const progressBar = document.getElementById('playerProgress');
            const timeDisplay = document.getElementById('playerTime');

            if (progressBar) progressBar.style.width = '0%';
            if (timeDisplay) timeDisplay.textContent = '0 / 0';

            this.updateCurrentValues();
            return;
        }

        const progress = (this.currentTimeIndex / (this.timeData.length - 1)) * 100;
        const progressBar = document.getElementById('playerProgress');
        const timeDisplay = document.getElementById('playerTime');

        if (progressBar) progressBar.style.width = `${progress}%`;
        if (timeDisplay) timeDisplay.textContent = `${this.currentTimeIndex + 1} / ${this.timeData.length}`;

        this.updateCurrentValues();
        this.highlightTableRow();
    }

    updateCurrentValues() {
        const container = document.getElementById('playerCurrentValues');
        if (!container || this.timeData.length === 0) return;

        const currentData = this.timeData[this.currentTimeIndex];
        let html = '';

        html += `
            <div class="data-point">
                <div class="data-label"><i class="fas fa-clock"></i> Время</div>
                <div class="data-value">${this.formatDateTime(currentData.timestamp)}</div>
            </div>
            <div class="data-point">
                <div class="data-label"><i class="fas fa-truck"></i> ТС</div>
                <div class="data-value">${currentData.vehicle_name || currentData.vehicle || '—'}</div>
            </div>
        `;

        // Показываем значения из активных графиков
        this.activeCharts.slice(0, 5).forEach(chart => {
            let value = 0;
            if (currentData.values && currentData.values[chart.param] !== undefined) {
                const val = currentData.values[chart.param];
                value = this.getNumericValue(val);
            }

            html += `
                <div class="data-point">
                    <div class="data-label"><i class="fas fa-chart-line"></i> ${chart.name}</div>
                    <div class="data-value">${value.toFixed(2)}</div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    highlightTableRow() {
        const rows = document.querySelectorAll('#dataTableBody tr');
        rows.forEach((row, index) => {
            row.classList.toggle('active', index === this.currentTimeIndex);
        });
    }

    // ============================================
    // УПРАВЛЕНИЕ ГРАФИКАМИ
    // ============================================
    setupChartControls() {
        const zoomInBtn = document.getElementById('chartZoomIn');
        const zoomOutBtn = document.getElementById('chartZoomOut');
        const chartPrevBtn = document.getElementById('chartPrev');
        const chartNextBtn = document.getElementById('chartNext');
        const chartTypeSelect = document.getElementById('chartTypeSelect');

        if (zoomInBtn) zoomInBtn.addEventListener('click', () => this.zoomIn());
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => this.zoomOut());
        if (chartPrevBtn) chartPrevBtn.addEventListener('click', () => this.chartPrev());
        if (chartNextBtn) chartNextBtn.addEventListener('click', () => this.chartNext());

        if (chartTypeSelect) {
            chartTypeSelect.addEventListener('change', (e) => {
                // Обновляем тип для всех активных графиков
                this.activeCharts.forEach(chart => {
                    chart.type = e.target.value;
                });

                if (this.timeData.length > 0 && this.activeCharts.length > 0) {
                    this.createCombinedChart();
                }
            });
        }

        const zoomSlider = document.getElementById('chartZoomSlider');
        const rangeSlider = document.getElementById('chartRangeSlider');

        if (zoomSlider) {
            zoomSlider.addEventListener('input', (e) => {
                this.zoomLevel = parseInt(e.target.value);
                this.updateZoom();
            });
        }

        if (rangeSlider) {
            rangeSlider.addEventListener('input', (e) => {
                this.chartOffset = parseInt(e.target.value);
                this.updateChartView();
            });
        }

        // Настройка переключения показа всех данных
        const showAllSwitch = document.getElementById('showAllDataSwitch');
        if (showAllSwitch) {
            showAllSwitch.addEventListener('change', (e) => {
                this.showAllData = e.target.checked;
                this.renderDataTable();
            });
        }
    }

    setupTabSwitching() {
        // Установка обработчиков для кнопок вкладок
        const tabs = ['charts', 'table', 'multi'];

        tabs.forEach(tab => {
            const btn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
            if (btn) {
                btn.addEventListener('click', () => this.switchTab(tab));
            }
        });
    }

    updateChartControls() {
        const zoomSlider = document.getElementById('chartZoomSlider');
        const rangeSlider = document.getElementById('chartRangeSlider');

        if (zoomSlider) {
            zoomSlider.value = this.zoomLevel;
        }

        if (rangeSlider && this.timeData.length > 0) {
            const maxOffset = Math.max(0, this.timeData.length - Math.floor(this.timeData.length * (this.zoomLevel / 100)));
            rangeSlider.max = maxOffset;
            rangeSlider.value = this.chartOffset;
        }
    }

    updateChartRangeInfo() {
        if (this.timeData.length === 0) {
            const rangeInfo = document.getElementById('chartRangeInfo');
            if (rangeInfo) {
                rangeInfo.textContent = 'Нет данных';
            }
            return;
        }

        const start = this.chartOffset;
        const visibleCount = Math.floor(this.timeData.length * (this.zoomLevel / 100));
        const end = Math.min(start + visibleCount, this.timeData.length);
        const total = this.timeData.length;

        const rangeInfo = document.getElementById('chartRangeInfo');
        if (rangeInfo) {
            rangeInfo.textContent = `Записи ${start + 1}-${end} из ${total} (${this.zoomLevel}%)`;
        }
    }

    zoomIn() {
        if (this.zoomLevel > 10) {
            this.zoomLevel = Math.max(10, this.zoomLevel - 10);
            this.updateChartView();
        }
    }

    zoomOut() {
        if (this.zoomLevel < 100) {
            this.zoomLevel = Math.min(100, this.zoomLevel + 10);
            this.updateChartView();
        }
    }

    updateZoom() {
        this.updateChartView();
    }

    chartPrev() {
        const visibleCount = Math.floor(this.timeData.length * (this.zoomLevel / 100));
        const step = Math.max(1, Math.floor(visibleCount / 10));

        if (this.chartOffset > 0) {
            this.chartOffset = Math.max(0, this.chartOffset - step);
            this.updateChartView();
        }
    }

    chartNext() {
        const visibleCount = Math.floor(this.timeData.length * (this.zoomLevel / 100));
        const step = Math.max(1, Math.floor(visibleCount / 10));

        if (this.chartOffset + visibleCount < this.timeData.length) {
            this.chartOffset = Math.min(
                this.timeData.length - visibleCount,
                this.chartOffset + step
            );
            this.updateChartView();
        }
    }

    updateChartView() {
        if (this.timeData.length === 0 || this.activeCharts.length === 0) return;

        // Здесь можно реализовать обновление отображаемой области графика
        // В текущей реализации показываются все данные
        this.updateChartControls();
        this.updateChartRangeInfo();
    }

    // ============================================
    // СТАТИСТИКА И ОТЧЕТЫ
    // ============================================
    updateStatistics(data) {
        const summary = data.historical_data?.summary || {};
        const parameterStats = summary.parameter_stats || {};

        // Обновляем статистику на основе данных
        const updateIfExists = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        // Пробег
        const distance = parameterStats.TotalDistance?.sum || 0;
        updateIfExists('statDistance', distance.toLocaleString('ru-RU', {maximumFractionDigits: 0}));

        // Расход топлива
        const fuel = parameterStats.Engine1FuelConsum?.sum || 0;
        updateIfExists('statFuel', fuel.toLocaleString('ru-RU', {maximumFractionDigits: 0}));

        // Рейтинг
        const rating = parameterStats.DQRating?.avg || 0;
        updateIfExists('statRating', rating.toFixed(1));

        // Время (моточасы)
        const hours = parameterStats.Engine1Motohours?.sum || 0;
        updateIfExists('statHours', hours.toFixed(1));

        // Показываем секцию статистики
        const statsSection = document.getElementById('statsSection');
        if (statsSection) {
            statsSection.style.display = 'block';
        }
    }

    // ============================================
    // ЭКСПОРТ ДАННЫХ
    // ============================================
    exportData(format) {
        if (this.timeData.length === 0) {
            this.showNotification('Нет данных для экспорта', 'warning');
            return;
        }

        let data, mimeType, filename;

        switch (format) {
            case 'csv':
                data = this.convertToCSV();
                mimeType = 'text/csv;charset=utf-8;';
                filename = `данные-тс-${new Date().toISOString().slice(0, 10)}.csv`;
                break;

            case 'json':
                data = JSON.stringify(this.timeData, null, 2);
                mimeType = 'application/json';
                filename = `данные-тс-${new Date().toISOString().slice(0, 10)}.json`;
                break;

            case 'excel':
                data = this.convertToExcel();
                mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
                filename = `данные-тс-${new Date().toISOString().slice(0, 10)}.xlsx`;
                break;

            default:
                this.showNotification('Неподдерживаемый формат экспорта', 'error');
                return;
        }

        const blob = new Blob([data], { type: mimeType });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showNotification(`Данные экспортированы в ${format.toUpperCase()}`, 'success');
    }

    convertToCSV() {
        // Собираем все уникальные параметры
        const allParams = new Set();
        this.timeData.forEach(item => {
            if (item.values) {
                Object.keys(item.values).forEach(param => allParams.add(param));
            }
        });

        const sortedParams = Array.from(allParams).sort();

        // Заголовки
        const headers = ['Время', 'ТС', 'Идентификатор ТС', 'Тип записи', ...sortedParams];

        // Данные
        const rows = this.timeData.map(item => {
            const row = [
                `"${item.timestamp || ''}"`,
                `"${item.vehicle_name || item.vehicle || ''}"`,
                `"${item.vehicle_id || ''}"`,
                `"${item.type || item.stage || ''}"`
            ];

            sortedParams.forEach(param => {
                let value = '';
                if (item.values && item.values[param] !== undefined) {
                    const val = item.values[param];
                    if (typeof val === 'string' && val.includes(':')) {
                        value = this.formatTimeToHours(val);
                    } else {
                        value = this.getNumericValue(val);
                    }
                }
                row.push(value);
            });

            return row;
        });

        // Объединяем заголовки и данные
        const csvContent = [headers, ...rows]
            .map(row => row.join(','))
            .join('\n');

        return csvContent;
    }

    convertToExcel() {
        // Для простоты создаем CSV, который можно открыть в Excel
        return this.convertToCSV();
    }

    // ============================================
    // УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
    // ============================================
    formatTimeToHours(timeStr) {
        if (!timeStr || typeof timeStr !== 'string') return 0;

        try {
            const parts = timeStr.split(':');
            if (parts.length === 3) {
                const hours = parseFloat(parts[0]) || 0;
                const minutes = parseFloat(parts[1]) || 0;
                const seconds = parseFloat(parts[2]) || 0;
                return hours + (minutes / 60) + (seconds / 3600);
            }
        } catch (e) {
            console.warn('Ошибка преобразования времени:', e);
        }

        return 0;
    }

    formatDateTime(timestamp) {
        if (!timestamp) return '—';

        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return timestamp;

            return date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return timestamp;
        }
    }

    formatDateOnly(timestamp) {
        if (!timestamp) return '—';

        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return timestamp;

            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        } catch {
            return timestamp;
        }
    }

    showLoading(title, message) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            document.getElementById('loadingTitle').textContent = title;
            document.getElementById('loadingMessage').textContent = message;
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    updateProgress(percent, message = '') {
        const progress = document.getElementById('loadingProgress');
        if (progress) progress.style.width = percent + '%';

        if (message) {
            const messageEl = document.getElementById('loadingMessage');
            if (messageEl) messageEl.textContent = message;
        }
    }

    showNotification(message, type = 'info') {
        console.log(`[NOTIFICATION ${type.toUpperCase()}] ${message}`);

        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const alertClass = {
            success: 'alert-success',
            error: 'alert-error',
            warning: 'alert-warning',
            info: 'alert-info'
        }[type];

        const alert = document.createElement('div');
        alert.className = `alert ${alertClass}`;
        alert.innerHTML = `
            <div class="alert-icon"><i class="fas ${icons[type]}"></i></div>
            <div class="alert-content"><p>${message}</p></div>
            <button class="alert-close" onclick="this.parentElement.remove()"><i class="fas fa-times"></i></button>
        `;

        container.appendChild(alert);

        // Автоматическое удаление уведомления через 5 секунд
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // ============================================
    // УПРАВЛЕНИЕ ТС
    // ============================================
    renderVehiclesList() {
        const container = document.getElementById('vehiclesList');
        if (!container) return;

        if (this.vehicles.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-car fa-2x text-muted mb-3"></i>
                    <p class="text-muted mb-0">ТС не найдены</p>
                </div>
            `;
            return;
        }

        let html = '';
        this.vehicles.forEach(vehicle => {
            const isSelected = this.selectedVehicles.includes(vehicle.id);

            html += `
                <div class="vehicle-item ${isSelected ? 'selected' : ''}"
                     onclick="analyzer.toggleVehicle('${vehicle.id}')">
                    <div class="vehicle-icon"><i class="fas fa-truck"></i></div>
                    <div class="vehicle-info">
                        <div class="vehicle-name">${vehicle.name}</div>
                        <div class="vehicle-plate">${vehicle.license_plate || '—'}</div>
                    </div>
                    <div class="vehicle-check">
                        <i class="fas fa-${isSelected ? 'check-circle' : 'circle'}"></i>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        this.updateVehicleCount();
        this.updateLoadButton();
    }

    toggleVehicle(vehicleId) {
        const index = this.selectedVehicles.indexOf(vehicleId);

        if (index > -1) {
            this.selectedVehicles.splice(index, 1);
        } else {
            this.selectedVehicles.push(vehicleId);
        }

        this.renderVehiclesList();
    }

    selectAllVehicles() {
        this.selectedVehicles = this.vehicles.map(v => v.id);
        this.renderVehiclesList();
        this.showNotification('Все ТС выбраны', 'success');
    }

    deselectAllVehicles() {
        this.selectedVehicles = [];
        this.renderVehiclesList();
        this.showNotification('Выбор ТС сброшен', 'info');
    }

    searchVehicles(query) {
        const container = document.getElementById('vehiclesList');
        if (!container) return;

        const searchLower = query.toLowerCase();
        const filtered = this.vehicles.filter(vehicle =>
            vehicle.name.toLowerCase().includes(searchLower) ||
            (vehicle.license_plate && vehicle.license_plate.toLowerCase().includes(searchLower))
        );

        let html = '';

        filtered.forEach(vehicle => {
            const isSelected = this.selectedVehicles.includes(vehicle.id);

            html += `
                <div class="vehicle-item ${isSelected ? 'selected' : ''}"
                     onclick="analyzer.toggleVehicle('${vehicle.id}')">
                    <div class="vehicle-icon"><i class="fas fa-truck"></i></div>
                    <div class="vehicle-info">
                        <div class="vehicle-name">${vehicle.name}</div>
                        <div class="vehicle-plate">${vehicle.license_plate || '—'}</div>
                    </div>
                    <div class="vehicle-check">
                        <i class="fas fa-${isSelected ? 'check-circle' : 'circle'}"></i>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html || `
            <div class="text-center py-4">
                <i class="fas fa-search fa-2x text-muted mb-3"></i>
                <p class="text-muted mb-0">ТС не найдены</p>
            </div>
        `;
    }

    setPeriod(days) {
        const toDate = new Date();
        const fromDate = new Date();
        fromDate.setDate(toDate.getDate() - days);

        const dateFromEl = document.getElementById('dateFrom');
        const dateToEl = document.getElementById('dateTo');

        if (dateFromEl) {
            dateFromEl.value = fromDate.toISOString().split('T')[0];
        }

        if (dateToEl) {
            dateToEl.value = toDate.toISOString().split('T')[0];
        }

        this.updateLoadButton();
    }

    updateLoadButton() {
        const hasVehicles = this.selectedVehicles.length > 0;
        const dateFromEl = document.getElementById('dateFrom');
        const dateToEl = document.getElementById('dateTo');
        const hasDates = dateFromEl && dateFromEl.value && dateToEl && dateToEl.value;
        const loadBtn = document.getElementById('loadDataBtn');

        if (loadBtn) {
            loadBtn.disabled = !hasVehicles || !hasDates;
        }
    }

    updateVehicleCount() {
        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.textContent = this.selectedVehicles.length;
        }
    }

    selectTableRow(index) {
        this.currentTimeIndex = index;
        this.updatePlayerDisplay();
        this.pause();
    }

    // ============================================
    // ОБРАБОТЧИКИ СОБЫТИЙ
    // ============================================
    setupEventListeners() {
        // Даты
        const dateFromEl = document.getElementById('dateFrom');
        const dateToEl = document.getElementById('dateTo');

        if (dateFromEl) {
            dateFromEl.addEventListener('change', () => this.updateLoadButton());
        }

        if (dateToEl) {
            dateToEl.addEventListener('change', () => this.updateLoadButton());
        }

        // Периоды
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const days = parseInt(btn.dataset.days);
                this.setPeriod(days);

                document.querySelectorAll('.period-btn').forEach(b => {
                    b.classList.remove('active');
                });

                btn.classList.add('active');
            });
        });

        // Выбор параметра графика
        const paramSelect = document.getElementById('chartParamSelect');
        if (paramSelect) {
            paramSelect.addEventListener('change', () => {
                // Автоматически устанавливаем цвет для выбранного параметра
                const selectedParam = paramSelect.value;
                if (selectedParam && this.paramColors.has(selectedParam)) {
                    const color = this.paramColors.get(selectedParam);
                    const colorSelect = document.getElementById('chartColorSelect');
                    if (colorSelect) {
                        colorSelect.value = color;
                    }
                }
            });
        }

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.loadData();
            }

            if (e.key === ' ') {
                e.preventDefault();
                this.togglePlay();
            }

            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.prev();
            }

            if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.next();
            }

            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                this.exportData('csv');
            }

            if (e.ctrlKey && e.key === 'j') {
                e.preventDefault();
                this.exportData('json');
            }
        });

        // Выбор цвета
        const colorSelect = document.getElementById('chartColorSelect');
        if (colorSelect) {
            colorSelect.addEventListener('change', (e) => {
                // При изменении цвета в поле, обновляем выбранный параметр
                const paramSelect = document.getElementById('chartParamSelect');
                if (paramSelect && paramSelect.value) {
                    this.paramColors.set(paramSelect.value, e.target.value);

                    // Обновляем цвет в активных графиках
                    const activeChart = this.activeCharts.find(chart => chart.param === paramSelect.value);
                    if (activeChart) {
                        activeChart.color = e.target.value;
                        this.updateActiveChartsDisplay();
                        this.createCombinedChart();
                    }
                }
            });
        }
    }
}

// Глобальный экземпляр
window.analyzer = new EnhancedVehicleAnalyzer();

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Инициализация улучшенного анализатора ТС');
    window.analyzer.init();
});