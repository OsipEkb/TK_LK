/**
 * VehiclesAnalyzer - Комплексный анализ исторических данных ТС
 * Использует данные AutoGRAPH API для анализа транспортных средств
 */

class VehiclesAnalyzer {
    constructor() {
        this.vehicles = [];
        this.filteredVehicles = [];
        this.selectedVehicles = [];
        this.historicalData = null;
        this.charts = new Map();
        this.playerInterval = null;
        this.isPlaying = false;
        this.currentTimeIndex = 0;
        this.playerSpeed = 1;
        this.allTrips = [];
        this.selectedParam = null;

        // Группы параметров для анализа
        this.paramGroups = [
            {
                id: 'mileage_speed',
                name: 'Пробег и скорость',
                icon: 'fa-tachometer-alt',
                params: [
                    { id: 'TotalDistance', name: 'Пробег', unit: 'км' },
                    { id: 'AverageSpeed', name: 'Средняя скорость', unit: 'км/ч' },
                    { id: 'MaxSpeed', name: 'Максимальная скорость', unit: 'км/ч' },
                    { id: 'OverspeedCount', name: 'Превышения скорости', unit: 'раз' }
                ]
            },
            {
                id: 'fuel',
                name: 'Расход топлива',
                icon: 'fa-gas-pump',
                params: [
                    { id: 'Engine1FuelConsum', name: 'Расход топлива', unit: 'л' },
                    { id: 'Engine1FuelConsumMPer100km', name: 'Расход на 100км', unit: 'л/100км' },
                    { id: 'TankMainFuelLevel First', name: 'Уровень на начало', unit: 'л' },
                    { id: 'TankMainFuelLevel Last', name: 'Уровень на конец', unit: 'л' }
                ]
            },
            {
                id: 'engine',
                name: 'Работа двигателя',
                icon: 'fa-cogs',
                params: [
                    { id: 'Engine1Motohours', name: 'Моточасы', unit: 'ч' },
                    { id: 'Engine1MHOnParks', name: 'Холостая работа', unit: 'ч' },
                    { id: 'Engine1MHInMove', name: 'Полезная работа', unit: 'ч' },
                    { id: 'Engine1FuelConsumDuringMH', name: 'Расход при работе', unit: 'л/ч' }
                ]
            },
            {
                id: 'safety',
                name: 'Безопасность',
                icon: 'fa-shield-alt',
                params: [
                    { id: 'DQRating', name: 'Рейтинг вождения', unit: '%' },
                    { id: 'DQExcessAccelPoints', name: 'Резкие ускорения', unit: 'шт' },
                    { id: 'DQExcessBrakePoints', name: 'Резкие торможения', unit: 'шт' },
                    { id: 'DQEmergencyBrakePoints', name: 'Аварийные торможения', unit: 'шт' }
                ]
            },
            {
                id: 'time',
                name: 'Время и остановки',
                icon: 'fa-clock',
                params: [
                    { id: 'TotalDuration', name: 'Общее время', unit: 'ч' },
                    { id: 'MoveDuration', name: 'Время движения', unit: 'ч' },
                    { id: 'ParkDuration', name: 'Время стоянки', unit: 'ч' },
                    { id: 'ParkCount', name: 'Количество остановок', unit: 'раз' }
                ]
            }
        ];
    }

    // ============================================
    // ИНИЦИАЛИЗАЦИЯ
    // ============================================
    async init() {
        console.log('🚀 Инициализация анализа ТС');

        try {
            await this.loadVehicles();
            this.renderParamGroups();
            this.setupEventListeners();
            this.setupPlayer();
            this.initTabs();

            this.showNotification('Система анализа готова к работе', 'info');

        } catch (error) {
            console.error('Ошибка инициализации:', error);
            this.showNotification('Ошибка инициализации: ' + error.message, 'error');
        }
    }

    // ============================================
    // ЗАГРУЗКА ДАННЫХ
    // ============================================
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

            if (!response.ok) {
                throw new Error(`HTTP ошибка ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.vehicles = data.data.vehicles;
                this.filteredVehicles = [...this.vehicles];
                console.log(`✅ Загружено ТС: ${this.vehicles.length}`);
                this.renderVehiclesList();
                this.showNotification(`Загружено ${this.vehicles.length} ТС`, 'success');
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

    async loadHistoricalData() {
        if (this.selectedVehicles.length === 0) {
            this.showNotification('Выберите хотя бы одно ТС', 'warning');
            return;
        }

        const startDate = document.getElementById('dateFrom').value;
        const endDate = document.getElementById('dateTo').value;

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

            const response = await fetch('/vehicles/api/get-historical-data/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    vehicle_ids: this.selectedVehicles,
                    start_date: startDate,
                    end_date: endDate
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ошибка: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.historicalData = data.data.historical_data;
                console.log('📊 Исторические данные:', this.historicalData);

                this.updateStatistics(data.data);
                this.renderSummary();
                this.renderDataTable();
                this.renderStagesTable();
                this.createCharts();
                this.updatePlayerData();
                this.showSections();

                this.showNotification(`Данные успешно загружены`, 'success');

            } else {
                throw new Error(data.error || 'Ошибка загрузки данных');
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки данных:', error);
            this.showNotification('Ошибка загрузки: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // ============================================
    // ОТОБРАЖЕНИЕ ДАННЫХ
    // ============================================
    renderVehiclesList() {
        const container = document.getElementById('vehiclesList');
        if (!container) return;

        if (this.filteredVehicles.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-car fa-2x text-muted mb-3"></i>
                    <p class="text-muted mb-0">ТС не найдены</p>
                </div>
            `;
            return;
        }

        let html = '';
        this.filteredVehicles.forEach(vehicle => {
            const isSelected = this.selectedVehicles.includes(vehicle.id);
            html += `
                <div class="vehicle-item ${isSelected ? 'selected' : ''}"
                     onclick="analyzer.toggleVehicle('${vehicle.id}')">
                    <div class="vehicle-icon">
                        <i class="fas fa-truck"></i>
                    </div>
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

    renderParamGroups() {
        const container = document.getElementById('paramGroups');
        if (!container) return;

        let html = '';
        this.paramGroups.forEach(group => {
            html += `
                <div class="param-group">
                    <div class="param-group-header">
                        <div class="param-group-icon">
                            <i class="fas ${group.icon}"></i>
                        </div>
                        <h6 class="param-group-title">${group.name}</h6>
                    </div>
                    <div class="param-group-body">
            `;

            group.params.forEach(param => {
                html += `
                    <div class="param-item" onclick="analyzer.selectParam('${param.id}')">
                        <div class="param-checkbox">
                            <i class="far fa-circle"></i>
                        </div>
                        <div class="param-info">
                            <div class="param-name">${param.name}</div>
                            <div class="param-unit">${param.unit}</div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    renderSummary() {
        const container = document.getElementById('summaryContainer');
        if (!container || !this.historicalData?.vehicles) return;

        let html = `
            <div class="row">
                <div class="col-md-12">
                    <div class="summary-header mb-4">
                        <h4 class="text-gold">Сводка по транспортным средствам</h4>
                        <p class="text-light opacity-75">Период: ${this.historicalData.period?.start} - ${this.historicalData.period?.end}</p>
                    </div>
                </div>
            </div>
            
            <div class="row">
        `;

        Object.entries(this.historicalData.vehicles).forEach(([vehicleId, vehicleData]) => {
            const summary = vehicleData.summary || {};
            const stats = vehicleData.statistics || {};

            html += `
                <div class="col-md-6 mb-4">
                    <div class="vehicle-summary-card">
                        <div class="vehicle-summary-header">
                            <h5 class="vehicle-summary-title">${vehicleData.name}</h5>
                            <span class="badge bg-gold text-dark">${vehicleData.statistics?.trips_count || 0} поездок</span>
                        </div>
                        
                        <div class="vehicle-summary-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-road me-2"></i>Пробег
                                        </div>
                                        <div class="summary-stat-value">${this.formatNumber(summary.distance || 0)} км</div>
                                    </div>
                                    
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-gas-pump me-2"></i>Расход топлива
                                        </div>
                                        <div class="summary-stat-value">${this.formatNumber(summary.fuel || 0)} л</div>
                                    </div>
                                    
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-tachometer-alt me-2"></i>Ср. скорость
                                        </div>
                                        <div class="summary-stat-value">${this.formatNumber(summary.avg_speed || 0)} км/ч</div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-star me-2"></i>Рейтинг
                                        </div>
                                        <div class="summary-stat-value">${this.formatNumber(summary.avg_rating || 0)}%</div>
                                    </div>
                                    
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-clock me-2"></i>Моточасы
                                        </div>
                                        <div class="summary-stat-value">${this.formatNumber(summary.motohours || 0)} ч</div>
                                    </div>
                                    
                                    <div class="summary-stat">
                                        <div class="summary-stat-label">
                                            <i class="fas fa-car me-2"></i>Поездок
                                        </div>
                                        <div class="summary-stat-value">${vehicleData.statistics?.trips_count || 0}</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="vehicle-summary-footer mt-3">
                                <button class="btn btn-sm btn-outline-gold" onclick="analyzer.showVehicleDetails('${vehicleId}')">
                                    <i class="fas fa-chart-line me-1"></i>Детали
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        container.innerHTML = html;
    }

    renderDataTable() {
        const container = document.getElementById('dataTableBody');
        const countElement = document.getElementById('detailsCount');

        if (!container || !this.historicalData?.vehicles) {
            container.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-database fa-2x text-muted"></i>
                        <p class="text-muted mt-2">Нет данных</p>
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';
        let rowCount = 0;

        Object.entries(this.historicalData.vehicles).forEach(([vehicleId, vehicleData]) => {
            const tableData = vehicleData.table_data || [];

            tableData.forEach(row => {
                html += `
                    <tr onclick="analyzer.selectTrip(${rowCount})">
                        <td>${vehicleData.name}</td>
                        <td>${row.date || row.dt || ''}</td>
                        <td class="text-end">${this.formatNumber(row.distance || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(row.speed || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(row.max_speed || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(row.fuel || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(row.rating || 0, 1)}</td>
                        <td><span class="badge ${row.type === 'trip' ? 'bg-primary' : 'bg-secondary'}">${row.type === 'trip' ? 'Поездка' : 'За день'}</span></td>
                    </tr>
                `;
                rowCount++;
            });
        });

        if (!html) {
            html = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-database fa-2x text-muted"></i>
                        <p class="text-muted mt-2">Нет данных для отображения</p>
                    </td>
                </tr>
            `;
        }

        container.innerHTML = html;
        countElement.textContent = `${rowCount} записей`;

        // Сохраняем данные для плеера
        this.allTrips = [];
        Object.values(this.historicalData.vehicles).forEach(vehicle => {
            vehicle.table_data?.forEach(row => {
                this.allTrips.push({
                    ...row,
                    vehicleName: vehicle.name
                });
            });
        });
    }

    renderStagesTable() {
        const container = document.getElementById('stagesTableBody');
        if (!container || !this.historicalData?.vehicles) return;

        let html = '';

        Object.entries(this.historicalData.vehicles).forEach(([vehicleId, vehicleData]) => {
            const rawStages = vehicleData.raw_stages || [];

            rawStages.forEach(stage => {
                html += `
                    <tr>
                        <td>${vehicleData.name}</td>
                        <td><span class="badge bg-info">${stage.stage || ''}</span></td>
                        <td>${this.formatDate(stage.dt || '')}</td>
                        <td>${stage.duration || ''}</td>
                        <td class="text-end">${this.formatNumber(stage.TotalDistance || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(stage.AverageSpeed || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(stage.Engine1FuelConsum || 0, 1)}</td>
                        <td class="text-end">${this.formatNumber(stage.DQRating || 0, 1)}</td>
                    </tr>
                `;
            });
        });

        if (!html) {
            html = `
                <tr>
                    <td colspan="8" class="text-center py-5">
                        <i class="fas fa-list fa-2x text-muted mb-3"></i>
                        <p class="text-muted mb-0">Нет данных о стадиях</p>
                    </td>
                </tr>
            `;
        }

        container.innerHTML = html;
    }

    // ============================================
    // ГРАФИКИ И АНАЛИЗ
    // ============================================
    createCharts() {
        // Уничтожить старые диаграммы
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();

        // Создать 4 основные диаграммы
        this.createChart('chart1', 'TotalDistance', 'bar', 'Пробег по ТС (км)');
        this.createChart('chart2', 'AverageSpeed', 'line', 'Средняя скорость (км/ч)');
        this.createChart('chart3', 'Engine1FuelConsum', 'horizontalBar', 'Расход топлива (л)');
        this.createChart('chart4', 'DQRating', 'radar', 'Рейтинг вождения (%)');

        // Создать главную диаграмму если выбран параметр
        if (this.selectedParam) {
            this.updateMainChart();
        }
    }

    createChart(canvasId, param, type, title) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !this.historicalData) return;

        const ctx = canvas.getContext('2d');
        const data = this.prepareChartData(param, type);

        if (!data) return;

        const chart = new Chart(ctx, {
            type: type === 'horizontalBar' ? 'bar' : type,
            data: data,
            options: this.getChartOptions(type, title)
        });

        this.charts.set(canvasId, chart);
    }

    updateMainChart() {
        if (!this.selectedParam) {
            this.showNotification('Выберите параметр для построения графика', 'warning');
            return;
        }

        const param = this.paramGroups
            .flatMap(g => g.params)
            .find(p => p.id === this.selectedParam);

        if (!param) return;

        const chartType = document.querySelector('.chart-type-btn.active')?.dataset.type || 'line';
        this.createChart('mainChart', this.selectedParam, chartType, param.name);
    }

    prepareChartData(param, type) {
        if (!this.historicalData?.vehicles) return null;

        const datasets = [];
        const labels = [];
        const colors = ['#FFD700', '#FFED4E', '#D4AF37', '#B8860B', '#FFA500'];

        Object.entries(this.historicalData.vehicles).forEach(([vehicleId, vehicleData], index) => {
            const trips = vehicleData.trips_only_stats?.trips || [];
            if (trips.length === 0) return;

            const vehicle = this.vehicles.find(v => v.id === vehicleId);
            const vehicleName = vehicle?.name || `ТС ${vehicleId.substring(0, 8)}`;

            if (type === 'radar' || type === 'pie' || type === 'doughnut') {
                // Для радарных и круговых - средние значения
                const values = trips.map(t => t[param] || 0).filter(v => v > 0);
                if (values.length === 0) return;

                const avg = values.reduce((a, b) => a + b, 0) / values.length;

                if (labels.length === 0) {
                    labels.push(param);
                }

                datasets.push({
                    label: vehicleName,
                    data: [avg],
                    backgroundColor: colors[index % colors.length] + '40',
                    borderColor: colors[index % colors.length],
                    borderWidth: 2
                });
            } else {
                // Для линейных и столбчатых - все значения
                const data = trips.map(t => t[param] || 0);

                datasets.push({
                    label: vehicleName,
                    data: data,
                    borderColor: colors[index % colors.length],
                    backgroundColor: type === 'line' ? 'transparent' : colors[index % colors.length] + '40',
                    borderWidth: type === 'line' ? 3 : 2,
                    fill: type === 'line'
                });

                // Создать метки из дат
                if (labels.length === 0) {
                    trips.forEach((trip, i) => {
                        const date = trip.start_time || '';
                        if (date) {
                            try {
                                const d = new Date(date);
                                labels.push(`${d.getDate()}.${d.getMonth()+1} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`);
                            } catch {
                                labels.push(`Поездка ${i+1}`);
                            }
                        } else {
                            labels.push(`Поездка ${i+1}`);
                        }
                    });
                }
            }
        });

        if (datasets.length === 0) return null;

        return { labels, datasets };
    }

    getChartOptions(type, title) {
        const isHorizontal = type === 'horizontalBar';

        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: title,
                    color: '#FFD700',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    labels: {
                        color: '#FFFFFF',
                        font: { size: 12 }
                    }
                }
            },
            scales: type !== 'radar' && type !== 'pie' && type !== 'doughnut' ? {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#CCCCCC' },
                    title: {
                        display: isHorizontal,
                        text: 'Транспортные средства',
                        color: '#CCCCCC'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#CCCCCC' },
                    title: {
                        display: !isHorizontal,
                        text: 'Значение',
                        color: '#CCCCCC'
                    }
                }
            } : {},
            elements: {
                line: {
                    tension: 0.3
                }
            }
        };
    }

    // ============================================
    // ПЛЕЕР ДАННЫХ
    // ============================================
    setupPlayer() {
        const timeline = document.getElementById('playerTimeline');
        if (timeline) {
            timeline.addEventListener('click', (e) => {
                const rect = timeline.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                this.seekTo(percent);
            });
        }

        document.getElementById('playerPlay')?.addEventListener('click', () => this.togglePlay());
        document.getElementById('playerPause')?.addEventListener('click', () => this.pause());
        document.getElementById('playerStop')?.addEventListener('click', () => this.stop());
        document.getElementById('playerPrev')?.addEventListener('click', () => this.prev());
        document.getElementById('playerNext')?.addEventListener('click', () => this.next());

        const speedSelect = document.getElementById('playerSpeed');
        if (speedSelect) {
            speedSelect.addEventListener('change', (e) => {
                this.playerSpeed = parseFloat(e.target.value);
                if (this.isPlaying) {
                    this.startPlayback();
                }
            });
        }
    }

    updatePlayerData() {
        if (!this.historicalData) return;

        this.allTrips = [];
        Object.values(this.historicalData.vehicles).forEach(vehicle => {
            vehicle.table_data?.forEach(row => {
                this.allTrips.push({
                    ...row,
                    vehicleName: vehicle.name
                });
            });
        });

        this.allTrips.sort((a, b) => {
            const dateA = new Date(a.date || 0);
            const dateB = new Date(b.date || 0);
            return dateA - dateB;
        });

        this.currentTimeIndex = 0;
        this.updatePlayerDisplay();
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (!this.allTrips || this.allTrips.length === 0) return;

        this.isPlaying = true;
        document.getElementById('playerPlay').innerHTML = '<i class="fas fa-pause"></i>';
        this.startPlayback();
    }

    pause() {
        this.isPlaying = false;
        document.getElementById('playerPlay').innerHTML = '<i class="fas fa-play"></i>';
        this.stopPlayback();
    }

    stop() {
        this.pause();
        this.currentTimeIndex = 0;
        this.updatePlayerDisplay();
    }

    prev() {
        this.currentTimeIndex = Math.max(0, this.currentTimeIndex - 1);
        this.updatePlayerDisplay();
    }

    next() {
        this.currentTimeIndex = Math.min(this.allTrips.length - 1, this.currentTimeIndex + 1);
        this.updatePlayerDisplay();
    }

    seekTo(percent) {
        this.currentTimeIndex = Math.floor(percent * (this.allTrips.length - 1));
        this.updatePlayerDisplay();
    }

    startPlayback() {
        this.stopPlayback();

        this.playerInterval = setInterval(() => {
            this.currentTimeIndex = (this.currentTimeIndex + 1) % this.allTrips.length;
            this.updatePlayerDisplay();
        }, 1000 / this.playerSpeed);
    }

    stopPlayback() {
        if (this.playerInterval) {
            clearInterval(this.playerInterval);
            this.playerInterval = null;
        }
    }

    updatePlayerDisplay() {
        if (!this.allTrips || this.allTrips.length === 0) return;

        const trip = this.allTrips[this.currentTimeIndex];
        const progress = (this.currentTimeIndex / (this.allTrips.length - 1)) * 100;

        document.getElementById('playerProgress').style.width = `${progress}%`;
        document.getElementById('playerTime').textContent =
            `${this.currentTimeIndex + 1} / ${this.allTrips.length}`;

        this.updateTripDisplay(trip);
    }

    updateTripDisplay(trip) {
        const container = document.getElementById('playerData');
        if (!container || !trip) return;

        const html = `
            <div class="data-point">
                <span class="data-label">ТС:</span>
                <span class="data-value">${trip.vehicleName || '—'}</span>
            </div>
            <div class="data-point">
                <span class="data-label">Пробег:</span>
                <span class="data-value">${(trip.distance || 0).toFixed(1)} км</span>
            </div>
            <div class="data-point">
                <span class="data-label">Средняя скорость:</span>
                <span class="data-value">${(trip.speed || 0).toFixed(1)} км/ч</span>
            </div>
            <div class="data-point">
                <span class="data-label">Макс. скорость:</span>
                <span class="data-value">${(trip.max_speed || 0).toFixed(1)} км/ч</span>
            </div>
            <div class="data-point">
                <span class="data-label">Расход:</span>
                <span class="data-value">${(trip.fuel || 0).toFixed(1)} л</span>
            </div>
            <div class="data-point">
                <span class="data-label">Рейтинг:</span>
                <span class="data-value">${(trip.rating || 0).toFixed(1)}%</span>
            </div>
        `;

        container.innerHTML = html;
    }

    // ============================================
    // ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    // ============================================
    selectParam(paramId) {
        // Убрать выделение со всех параметров
        document.querySelectorAll('.param-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Добавить выделение выбранному
        event.currentTarget.classList.add('selected');
        this.selectedParam = paramId;

        // Если данные загружены, обновить диаграмму
        if (this.historicalData) {
            this.updateMainChart();
        }
    }

    selectTrip(index) {
        this.currentTimeIndex = index;
        this.updatePlayerDisplay();
        this.pause();
    }

    searchVehicles(query) {
        if (!query) {
            this.filteredVehicles = [...this.vehicles];
        } else {
            const searchLower = query.toLowerCase();
            this.filteredVehicles = this.vehicles.filter(vehicle =>
                vehicle.name.toLowerCase().includes(searchLower) ||
                (vehicle.license_plate && vehicle.license_plate.toLowerCase().includes(searchLower))
            );
        }
        this.renderVehiclesList();
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
        this.selectedVehicles = this.filteredVehicles.map(v => v.id);
        this.renderVehiclesList();
        this.showNotification('Все ТС выбраны', 'success');
    }

    deselectAllVehicles() {
        this.selectedVehicles = [];
        this.renderVehiclesList();
        this.showNotification('Выбор ТС сброшен', 'info');
    }

    setPeriod(days) {
        const toDate = new Date();
        const fromDate = new Date();
        fromDate.setDate(toDate.getDate() - days);

        document.getElementById('dateFrom').value = fromDate.toISOString().split('T')[0];
        document.getElementById('dateTo').value = toDate.toISOString().split('T')[0];
        this.updateLoadButton();
    }

    filterDetailsTable(query) {
        const tbody = document.getElementById('dataTableBody');
        const rows = tbody.getElementsByTagName('tr');

        for (let row of rows) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
        }
    }

    updateStatistics(data) {
        if (!this.historicalData?.summary) {
            document.getElementById('statsSection').style.display = 'none';
            return;
        }

        const summary = this.historicalData.summary;

        document.getElementById('statStages').textContent = summary.total_stages?.toLocaleString('ru-RU') || '0';
        document.getElementById('statDistance').textContent = summary.total_distance?.toLocaleString('ru-RU', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }) || '0';
        document.getElementById('statFuel').textContent = summary.total_fuel?.toLocaleString('ru-RU', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }) || '0';
        document.getElementById('statRating').textContent = summary.avg_rating?.toFixed(1) || '0';
        document.getElementById('statHours').textContent = summary.total_hours?.toFixed(1) || '0';

        document.getElementById('statsSection').style.display = 'block';
    }

    showSections() {
        ['statsSection', 'playerSection', 'chartsSection'].forEach(id => {
            const section = document.getElementById(id);
            if (section) section.style.display = 'block';
        });
    }

    initTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });

        const firstTab = document.querySelector('.tab-btn');
        if (firstTab) {
            this.switchTab(firstTab.dataset.tab);
        }
    }

    switchTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
        const activeContent = document.getElementById(`${tabId}Tab`);

        if (activeBtn) activeBtn.classList.add('active');
        if (activeContent) activeContent.classList.add('active');

        // Перерисовать диаграммы при переключении
        if (tabId === 'charts' && this.historicalData) {
            setTimeout(() => {
                this.charts.forEach(chart => chart.resize());
            }, 300);
        }
    }

    updateLoadButton() {
        const hasVehicles = this.selectedVehicles.length > 0;
        const hasDates = document.getElementById('dateFrom').value && document.getElementById('dateTo').value;
        const loadBtn = document.getElementById('loadDataBtn');

        if (loadBtn) {
            loadBtn.disabled = !hasVehicles || !hasDates;
        }
    }

    updateVehicleCount() {
        document.getElementById('selectedCount').textContent = this.selectedVehicles.length;
    }

    exportData(format) {
        if (!this.historicalData) {
            this.showNotification('Нет данных для экспорта', 'warning');
            return;
        }

        let data, mime, filename;

        if (format === 'csv') {
            data = this.convertToCSV();
            mime = 'text/csv;charset=utf-8;';
            filename = `данные-тс-${new Date().toISOString().slice(0,10)}.csv`;
        } else if (format === 'json') {
            data = JSON.stringify(this.historicalData, null, 2);
            mime = 'application/json';
            filename = `данные-тс-${new Date().toISOString().slice(0,10)}.json`;
        } else {
            return;
        }

        const blob = new Blob([data], { type: mime });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();

        this.showNotification(`Данные экспортированы в ${format.toUpperCase()}`, 'success');
    }

    convertToCSV() {
        const headers = ['ТС', 'Дата', 'Пробег (км)', 'Ср. скорость', 'Макс. скорость', 'Расход (л)', 'Рейтинг (%)', 'Тип'];
        const rows = [];

        Object.entries(this.historicalData.vehicles).forEach(([vehicleId, vehicleData]) => {
            const tableData = vehicleData.table_data || [];

            tableData.forEach(row => {
                rows.push([
                    vehicleData.name,
                    row.date || row.dt || '',
                    row.distance || 0,
                    row.speed || 0,
                    row.max_speed || 0,
                    row.fuel || 0,
                    row.rating || 0,
                    row.type === 'trip' ? 'Поездка' : 'За день'
                ]);
            });
        });

        return [headers, ...rows].map(row =>
            row.map(cell => `"${cell}"`).join(',')
        ).join('\n');
    }

    showVehicleDetails(vehicleId) {
        if (!this.historicalData?.vehicles?.[vehicleId]) return;

        const vehicleData = this.historicalData.vehicles[vehicleId];
        alert(`Детали по ТС: ${vehicleData.name}\nПробег: ${vehicleData.summary?.distance || 0} км\nРасход: ${vehicleData.summary?.fuel || 0} л`);
    }

    showStageAnalysis() {
        if (!this.historicalData?.vehicles) {
            this.showNotification('Нет данных для анализа', 'warning');
            return;
        }

        const modal = new bootstrap.Modal(document.getElementById('stagesAnalysisModal'));
        const canvas = document.getElementById('stagesChart');
        const statsContainer = document.getElementById('stagesStats');

        // Создаем график
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Движение', 'Стоянка', 'Двигатель', 'GPS'],
                datasets: [{
                    data: [40, 30, 20, 10],
                    backgroundColor: ['#FFD700', '#3498db', '#2ecc71', '#e74c3c'],
                    borderColor: '#1a1a1a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#FFFFFF',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });

        modal.show();
    }

    showDataStructure() {
        if (!this.historicalData) {
            this.showNotification('Нет данных для отображения', 'warning');
            return;
        }

        const modal = new bootstrap.Modal(document.getElementById('dataStructureModal'));
        const content = document.getElementById('dataStructureContent');
        const info = document.getElementById('dataStructureInfo');

        // Подготавливаем данные для отображения
        const displayData = {
            summary: this.historicalData.summary || {},
            vehicle_count: Object.keys(this.historicalData.vehicles || {}).length,
            total_stages: this.historicalData.total_stages || 0,
            data_type: this.historicalData.data_type || 'unknown',
            period: this.historicalData.period || {}
        };

        // Обновляем информацию
        info.innerHTML = `
            <div class="data-info-item">
                <div class="data-info-label">Тип данных:</div>
                <div class="data-info-value">${displayData.data_type}</div>
            </div>
            <div class="data-info-item">
                <div class="data-info-label">ТС:</div>
                <div class="data-info-value">${displayData.vehicle_count}</div>
            </div>
            <div class="data-info-item">
                <div class="data-info-label">Стадий:</div>
                <div class="data-info-value">${displayData.total_stages}</div>
            </div>
            <div class="data-info-item">
                <div class="data-info-label">Источники:</div>
                <div class="data-info-value">${this.historicalData.sources?.join(', ') || 'неизвестно'}</div>
            </div>
        `;

        // Отображаем структуру
        content.textContent = JSON.stringify(displayData, null, 2);
        modal.show();
    }

    formatDate(dateStr) {
        if (!dateStr) return '—';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('ru-RU') + ' ' +
                   date.toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
        } catch {
            return dateStr;
        }
    }

    formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) {
            return '—';
        }

        return value.toLocaleString('ru-RU', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    setupEventListeners() {
        // Даты
        document.getElementById('dateFrom')?.addEventListener('change', () => this.updateLoadButton());
        document.getElementById('dateTo')?.addEventListener('change', () => this.updateLoadButton());

        // Периоды
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const days = parseInt(btn.dataset.days);
                this.setPeriod(days);

                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Типы диаграмм
        document.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.chart-type-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const type = btn.dataset.type;
                if (this.selectedParam) {
                    this.createChart('mainChart', this.selectedParam, type, 'Диаграмма');
                }
            });
        });

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                this.loadHistoricalData();
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
        });
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
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const icon = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        }[type];

        const notification = document.createElement('div');
        notification.className = `alert ${type === 'error' ? 'alert-danger' : 
            type === 'success' ? 'alert-success' : 
            type === 'warning' ? 'alert-warning' : 'alert-info'} 
            alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas ${icon} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
        `;

        container.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Глобальный экземплярa
const analyzer = new VehiclesAnalyzer();

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    analyzer.init();
});