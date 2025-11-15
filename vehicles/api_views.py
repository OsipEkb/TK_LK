# vehicles/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from vehicles.services import AutoGraphService, AutoGraphHistoricalService
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class DebugAPIView(APIView):
    permission_classes = [AllowAny]  # Разрешаем доступ без аутентификации

    def get(self, request):
        """Диагностический endpoint для проверки работы API"""
        try:
            debug_info = {
                'status': 'diagnostics',
                'timestamp': datetime.now().isoformat(),
                'received_parameters': dict(request.GET),
                'service_status': {},
                'django_settings': {
                    'debug': getattr(settings, 'DEBUG', 'NOT_SET'),
                    'autograph_url': getattr(settings, 'AUTOGRAPH_API_BASE_URL', 'NOT_SET'),
                    'installed_apps': [app for app in getattr(settings, 'INSTALLED_APPS', []) if
                                       'vehicle' in app or 'rest' in app]
                }
            }

            # Проверяем базовый сервис
            try:
                base_service = AutoGraphService()
                login_result = base_service.login("Osipenko", "Osipenko")
                debug_info['service_status']['base_service'] = {
                    'login_success': login_result,
                    'token_available': bool(base_service.token),
                    'token_preview': base_service.token[:20] + '...' if base_service.token else None,
                    'base_url': base_service.base_url
                }

                if login_result:
                    schemas = base_service.get_schemas()
                    debug_info['service_status']['schemas'] = {
                        'count': len(schemas) if schemas else 0,
                        'first_schema': schemas[0] if schemas else None
                    }

                    # Пробуем получить список ТС
                    if schemas:
                        schema_id = schemas[0].get('ID')
                        vehicles_data = base_service.get_vehicles(schema_id)
                        debug_info['service_status']['vehicles'] = {
                            'schema_id': schema_id,
                            'items_count': len(vehicles_data.get('Items', [])) if vehicles_data else 0,
                            'sample_vehicles': []
                        }

                        # Добавляем примеры ТС
                        if vehicles_data and 'Items' in vehicles_data:
                            for vehicle in vehicles_data['Items'][:3]:
                                debug_info['service_status']['vehicles']['sample_vehicles'].append({
                                    'id': vehicle.get('ID'),
                                    'name': vehicle.get('Name'),
                                    'license_plate': base_service.extract_license_plate_enhanced(vehicle)
                                })
                else:
                    debug_info['service_status']['base_service']['error'] = 'Login failed'

            except Exception as e:
                debug_info['service_status']['base_service_error'] = str(e)
                import traceback
                debug_info['service_status']['base_service_traceback'] = traceback.format_exc()

            # Проверяем исторический сервис
            try:
                historical_service = AutoGraphHistoricalService()
                debug_info['service_status']['historical_service'] = {
                    'initialized': True,
                    'base_service_available': bool(historical_service.base_service)
                }

                # Пробуем получить тестовые исторические данные
                test_data = historical_service.get_vehicle_historical_statistics(
                    '11804e75-d2c3-4f2b-9107-5ad899adfe12',
                    'fad66447-fe18-4a2a-a7b9-945eab775fda',
                    '2024-01-01',
                    '2024-01-02'
                )
                debug_info['service_status']['historical_test'] = {
                    'success': bool(test_data),
                    'has_summary': bool(test_data and test_data.get('summary')),
                    'data_keys': list(test_data.keys()) if test_data else []
                }

                # Если есть ошибка, показываем ее
                if not test_data:
                    debug_info['service_status']['historical_test']['note'] = 'No data returned from historical service'

            except Exception as e:
                debug_info['service_status']['historical_service_error'] = str(e)
                import traceback
                debug_info['service_status']['historical_service_traceback'] = traceback.format_exc()

            return Response(debug_info)

        except Exception as e:
            logger.error(f"❌ Debug API error: {e}")
            return Response({
                'error': f'Debug failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=500)


class VehiclesListAPI(APIView):
    permission_classes = [AllowAny]  # Временно отключаем аутентификацию

    def get(self, request):
        """API для получения списка ТС"""
        try:
            logger.info("🔄 VEHICLES LIST API CALLED")

            service = AutoGraphService()
            if service.login("Osipenko", "Osipenko"):
                schemas = service.get_schemas()
                if schemas:
                    schema_id = schemas[0].get('ID')

                    # Получаем базовую информацию о ТС
                    vehicles_data = service.get_vehicles(schema_id)

                    if vehicles_data and 'Items' in vehicles_data:
                        formatted_vehicles = []
                        for vehicle in vehicles_data['Items']:
                            license_plate = service.extract_license_plate_enhanced(vehicle)
                            vehicle_info = {
                                'id': vehicle.get('ID'),
                                'name': vehicle.get('Name', 'Unknown'),
                                'license_plate': license_plate,
                                'serial': vehicle.get('Serial'),
                                'schema_id': schema_id,
                            }
                            formatted_vehicles.append(vehicle_info)

                        logger.info(f"✅ Successfully loaded {len(formatted_vehicles)} vehicles")
                        return Response({
                            'success': True,
                            'vehicles': formatted_vehicles,
                            'schema_id': schema_id,
                            'source': 'real_data',
                            'total_count': len(formatted_vehicles),
                        })

            # Fallback to mock data
            mock_vehicles = self.get_mock_vehicles()
            return Response({
                'success': True,
                'vehicles': mock_vehicles,
                'schema_id': 'mock-schema',
                'source': 'mock_data',
            })

        except Exception as e:
            logger.error(f"❌ Vehicles list API error: {e}")
            mock_vehicles = self.get_mock_vehicles()
            return Response({
                'success': True,
                'vehicles': mock_vehicles,
                'schema_id': 'error-schema',
                'source': 'error_fallback',
            })

    def get_mock_vehicles(self):
        """Генерация mock данных"""
        return [
            {
                'id': '11804e75-d2c3-4f2b-9107-5ad899adfe12',
                'name': '644 Freightliner',
                'license_plate': 'Н 644 ВК 186',
                'serial': '260668',
                'schema_id': 'fad66447-fe18-4a2a-a7b9-945eab775fda'
            },
            {
                'id': 'abe04e76-cf82-41ac-9836-086ae66e652e',
                'name': '776 Freightliner',
                'license_plate': 'Н 776 ВК 186',
                'serial': '261869',
                'schema_id': 'fad66447-fe18-4a2a-a7b9-945eab775fda'
            },
            {
                'id': '8570f4fd-ee21-431c-8412-9b4b54e955af',
                'name': '336 Freightliner',
                'license_plate': 'Н 336 ВК 186',
                'serial': '378356',
                'schema_id': 'fad66447-fe18-4a2a-a7b9-945eab775fda'
            }
        ]


class VehicleStatisticsAPI(APIView):
    permission_classes = [AllowAny]  # Временно отключаем аутентификацию

    def get(self, request):
        """GET метод для получения РЕАЛЬНЫХ исторических данных по ТС"""
        try:
            # Получаем параметры из GET запроса
            vehicle_id = request.GET.get('vehicle_id')
            schema_id = request.GET.get('schema_id', 'fad66447-fe18-4a2a-a7b9-945eab775fda')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            time_step = request.GET.get('time_step', 'hour')

            logger.info(f"🔄 GET Real historical data for: {vehicle_id} from {start_date} to {end_date}")

            if not all([vehicle_id, start_date, end_date]):
                return Response({
                    'success': False,
                    'error': 'Отсутствуют обязательные параметры: vehicle_id, start_date, end_date'
                }, status=400)

            # Детальное логирование параметров
            logger.info(
                f"📋 Parameters: vehicle_id={vehicle_id}, schema_id={schema_id}, start_date={start_date}, end_date={end_date}")

            # Пробуем получить реальные данные из AutoGRAPH
            real_data = self.get_real_historical_data(vehicle_id, schema_id, start_date, end_date)

            if real_data and real_data.get('summary'):
                logger.info(f"✅ Returning REAL data for {vehicle_id}")
                return Response({
                    'success': True,
                    'statistics': real_data,
                    'period': {
                        'start': start_date,
                        'end': end_date,
                        'step': time_step
                    },
                    'vehicle_id': vehicle_id,
                    'data_source': 'autograph_real'
                })

            # Fallback к mock данным
            logger.info(f"⚠️ No real data, using MOCK data for {vehicle_id}")
            mock_data = self.generate_mock_statistics(vehicle_id, start_date, end_date, time_step)

            # Проверяем что mock данные корректны
            if not mock_data or not mock_data.get('summary'):
                logger.error("❌ Mock data generation failed")
                return Response({
                    'success': False,
                    'error': 'Не удалось сгенерировать данные'
                }, status=500)

            return Response({
                'success': True,
                'statistics': mock_data,
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'step': time_step
                },
                'vehicle_id': vehicle_id,
                'data_source': 'mock_fallback'
            })

        except Exception as e:
            logger.error(f"❌ Vehicle statistics API error: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)

    def get_real_historical_data(self, vehicle_id, schema_id, start_date, end_date):
        """Получение реальных данных из AutoGRAPH"""
        try:
            logger.info(f"🔧 Attempting to get real data for {vehicle_id}")
            historical_service = AutoGraphHistoricalService()
            result = historical_service.get_vehicle_historical_statistics(
                vehicle_id, schema_id, start_date, end_date
            )
            logger.info(f"🔧 Real data result: {bool(result)}")
            if result:
                logger.info(f"🔧 Real data keys: {list(result.keys())}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting real historical data: {e}")
            import traceback
            logger.error(f"🔍 Traceback in get_real_historical_data: {traceback.format_exc()}")
            return None

    def generate_mock_statistics(self, vehicle_id, start_date, end_date, time_step):
        """Генерация mock данных"""
        try:
            vehicle_info = self.get_vehicle_info(vehicle_id)
            if not vehicle_info:
                logger.warning(f"⚠️ No vehicle info for {vehicle_id}")
                return None

            return self.generate_vehicle_specific_statistics(vehicle_info, start_date, end_date, time_step)
        except Exception as e:
            logger.error(f"❌ Error generating mock statistics: {e}")
            return None

    def get_vehicle_info(self, vehicle_id):
        """Получение информации о конкретном ТС"""
        vehicles_data = {
            '11804e75-d2c3-4f2b-9107-5ad899adfe12': {
                'id': '11804e75-d2c3-4f2b-9107-5ad899adfe12',
                'name': '644 Freightliner',
                'license_plate': 'Н 644 ВК 186',
                'serial': '260668',
                'type': 'Грузовой',
                'model': 'Freightliner'
            },
            'abe04e76-cf82-41ac-9836-086ae66e652e': {
                'id': 'abe04e76-cf82-41ac-9836-086ae66e652e',
                'name': '776 Freightliner',
                'license_plate': 'Н 776 ВК 186',
                'serial': '261869',
                'type': 'Грузовой',
                'model': 'Freightliner'
            },
            '8570f4fd-ee21-431c-8412-9b4b54e955af': {
                'id': '8570f4fd-ee21-431c-8412-9b4b54e955af',
                'name': '336 Freightliner',
                'license_plate': 'Н 336 ВК 186',
                'serial': '378356',
                'type': 'Грузовой',
                'model': 'Freightliner'
            }
        }

        return vehicles_data.get(vehicle_id)

    def generate_vehicle_specific_statistics(self, vehicle_info, start_date, end_date, time_step):
        """Генерация статистики для КОНКРЕТНОГО ТС"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            # Генерируем уникальные данные для каждого ТС на основе его ID
            vehicle_hash = hash(vehicle_info['id']) % 1000

            # Базовые данные, зависящие от конкретного ТС
            base_stats = {
                'total_distance': round(400 + (vehicle_hash % 600), 1),
                'total_fuel_consumption': round(150 + (vehicle_hash % 250), 1),
                'total_engine_hours': self.generate_vehicle_hours(vehicle_hash),
                'total_move_duration': self.generate_vehicle_duration(vehicle_hash, 0.7),
                'total_park_duration': self.generate_vehicle_duration(vehicle_hash, 0.3),
                'max_speed': round(75 + (vehicle_hash % 40), 1),
                'average_speed': round(45 + (vehicle_hash % 35), 1),
                'fuel_efficiency': round(25 + (vehicle_hash % 25), 1),
                'parking_count': 15 + (vehicle_hash % 20),
                'overspeed_count': 5 + (vehicle_hash % 15),
            }

            # Топливная аналитика
            fuel_analytics = {
                'current_level': round(300 + (vehicle_hash % 400), 1),
                'refills_count': 1 + (vehicle_hash % 3),
                'refills_volume': round(100 + (vehicle_hash % 200), 1),
                'consumption_per_motor_hour': round(20 + (vehicle_hash % 15), 1),
                'total_fuel_volume': round(400 + (vehicle_hash % 300), 1),
            }

            # Нарушения
            violations = {
                'overspeed_duration': self.generate_vehicle_duration(vehicle_hash, 0.1),
                'penalty_points': round(50 + (vehicle_hash % 100), 1),
                'overspeed_points': round(30 + (vehicle_hash % 70), 1),
            }

            # Статусы оборудования
            equipment_status = {
                'ignition': False,
                'gsm_signal': True,
                'gps_signal': True,
                'power': True,
                'movement': 'parking'
            }

            # Локация
            location = {
                'address': 'Технологическая ул., 25 с7, Сургут, Ханты-Мансийский АО — Югра',
                'coordinates': {'lat': 61.26816889, 'lng': 73.44545833},
                'last_update': datetime.now().isoformat()
            }

            # Генерация временных рядов для конкретного ТС
            time_series = self.generate_vehicle_time_series(vehicle_info, start, end, time_step, vehicle_hash)

            return {
                'summary': base_stats,
                'fuel_analytics': fuel_analytics,
                'violations': violations,
                'equipment_status': equipment_status,
                'location': location,
                'time_series': time_series,
                'vehicle_id': vehicle_info['id'],
                'vehicle_name': vehicle_info['name'],
                'license_plate': vehicle_info['license_plate'],
                'data_source': 'vehicle_specific'
            }
        except Exception as e:
            logger.error(f"❌ Error in generate_vehicle_specific_statistics: {e}")
            return None

    def generate_vehicle_hours(self, vehicle_hash):
        """Генерация часов работы для конкретного ТС"""
        base_hours = 25 + (vehicle_hash % 60)
        hours = int(base_hours)
        minutes = int((base_hours - hours) * 60)
        return f"{hours:02d}:{minutes:02d}:00"

    def generate_vehicle_duration(self, vehicle_hash, factor):
        """Генерация длительности для конкретного ТС"""
        base_hours = (15 + (vehicle_hash % 40)) * factor
        hours = int(base_hours)
        minutes = int((base_hours - hours) * 60)
        return f"{hours:02d}:{minutes:02d}:00"

    def generate_vehicle_time_series(self, vehicle_info, start, end, time_step, vehicle_hash):
        """Генерация временных рядов для конкретного ТС"""
        try:
            intervals = []
            current = start

            # Уникальные коэффициенты для каждого ТС
            distance_factor = 0.8 + (vehicle_hash % 40) / 100
            fuel_factor = 0.7 + (vehicle_hash % 50) / 100
            speed_factor = 0.9 + (vehicle_hash % 20) / 100
            fuel_volume_factor = 0.6 + (vehicle_hash % 80) / 100

            while current <= end:
                # Генерация данных с учетом характеристик ТС
                day_data = self.generate_vehicle_day_data(current, vehicle_hash, distance_factor, fuel_factor,
                                                          speed_factor,
                                                          fuel_volume_factor)

                interval_data = {
                    'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                    'distance': day_data['distance'],
                    'fuel_consumption': day_data['fuel'],
                    'engine_hours': day_data['hours'],
                    'move_duration': day_data['move_duration'],
                    'max_speed': day_data['speed'],
                    'fuel_level': day_data['fuel_level'],
                    'total_fuel_volume': day_data['total_fuel_volume'],
                }
                intervals.append(interval_data)

                if time_step == 'hour':
                    current += timedelta(hours=1)
                elif time_step == 'day':
                    current += timedelta(days=1)
                elif time_step == 'week':
                    current += timedelta(weeks=1)

            return intervals
        except Exception as e:
            logger.error(f"❌ Error generating vehicle time series: {e}")
            return []

    def generate_vehicle_day_data(self, date, vehicle_hash, distance_factor, fuel_factor, speed_factor,
                                  fuel_volume_factor):
        """Генерация дневных данных для конкретного ТС"""
        day_of_week = date.weekday()
        is_weekend = day_of_week >= 5

        # Базовые значения с учетом характеристик ТС
        if is_weekend:
            base_distance = 40 * distance_factor
            base_fuel = 15 * fuel_factor
            base_speed = 35 * speed_factor
            base_fuel_volume = 300 * fuel_volume_factor
        else:
            base_distance = 100 * distance_factor
            base_fuel = 35 * fuel_factor
            base_speed = 55 * speed_factor
            base_fuel_volume = 500 * fuel_volume_factor

        # Добавляем случайные вариации
        variation = random.uniform(-0.15, 0.15)

        return {
            'distance': round(base_distance * (1 + variation), 2),
            'fuel': round(base_fuel * (1 + variation), 2),
            'speed': round(base_speed * (1 + variation * 0.5), 2),
            'fuel_level': round(base_fuel_volume * 0.6 * (1 + variation), 2),
            'total_fuel_volume': round(base_fuel_volume * (1 + variation * 0.3), 2),
            'hours': self.generate_daily_hours(vehicle_hash, is_weekend),
            'move_duration': self.generate_daily_move_duration(vehicle_hash, is_weekend)
        }

    def generate_daily_hours(self, vehicle_hash, is_weekend):
        """Генерация дневных часов работы"""
        if is_weekend:
            hours = 1 + (vehicle_hash % 3)
        else:
            hours = 5 + (vehicle_hash % 5)
        minutes = random.randint(0, 59)
        return round(hours + minutes / 60, 2)

    def generate_daily_move_duration(self, vehicle_hash, is_weekend):
        """Генерация времени в движении"""
        if is_weekend:
            hours = 1 + (vehicle_hash % 2)
        else:
            hours = 3 + (vehicle_hash % 4)
        minutes = random.randint(0, 59)
        return round(hours + minutes / 60, 2)


class VehicleChartDataAPI(APIView):
    permission_classes = [AllowAny]  # Временно отключаем аутентификацию

    def get(self, request):
        """API для данных графиков с поддержкой стилей"""
        try:
            chart_type = request.GET.get('chart_type', 'composite')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            vehicle_id = request.GET.get('vehicle_id')
            chart_style = request.GET.get('chart_style', 'line')
            metrics = request.GET.get('metrics', '').split(',')

            if not start_date or not end_date or not vehicle_id:
                return Response({
                    'success': False,
                    'error': 'Отсутствуют start_date, end_date или vehicle_id'
                }, status=400)

            # Получаем реальные или mock данные
            chart_data = self.get_chart_data(vehicle_id, start_date, end_date, metrics, chart_style)

            return Response({
                'success': True,
                'chart_data': chart_data,
                'chart_type': chart_type,
                'chart_style': chart_style,
                'metrics': metrics
            })

        except Exception as e:
            logger.error(f"Chart data API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)

    def get_chart_data(self, vehicle_id, start_date, end_date, metrics, chart_style):
        """Получение данных для графиков"""
        try:
            historical_service = AutoGraphHistoricalService()
            time_series = historical_service.get_historical_time_series(
                'fad66447-fe18-4a2a-a7b9-945eab775fda',
                vehicle_id,
                start_date,
                end_date,
                metrics
            )

            if not time_series:
                time_series = self.generate_mock_time_series(start_date, end_date)

            return self.format_chart_data(time_series, metrics, chart_style)

        except Exception as e:
            logger.error(f"Error getting chart data: {e}")
            return self.generate_mock_chart_data(start_date, end_date, metrics, chart_style)

    def format_chart_data(self, time_series, metrics, chart_style):
        """Форматирование данных для графиков"""
        if not time_series:
            return {'labels': [], 'datasets': []}

        labels = [item['timestamp'] for item in time_series]

        metrics_config = {
            'distance': {'label': 'Пробег', 'unit': 'км', 'color': '#27ae60'},
            'fuel_consumption': {'label': 'Расход топлива', 'unit': 'л', 'color': '#e74c3c'},
            'max_speed': {'label': 'Скорость', 'unit': 'км/ч', 'color': '#3498db'},
            'engine_hours': {'label': 'Моточасы', 'unit': 'ч', 'color': '#f39c12'},
            'fuel_level': {'label': 'Уровень топлива', 'unit': 'л', 'color': '#9b59b6'},
            'total_fuel_volume': {'label': 'Общий объем топлива', 'unit': 'л', 'color': '#e67e22'},
        }

        datasets = []
        for metric in metrics:
            if metric in metrics_config:
                config = metrics_config[metric]
                data = [item.get(metric, 0) for item in time_series]

                dataset = {
                    'label': f"{config['label']} ({config['unit']})",
                    'data': data,
                    'borderColor': config['color'],
                    'backgroundColor': config['color'] + '20',
                    'tension': 0.4,
                }

                # Настройки в зависимости от стиля графика
                if chart_style == 'bar':
                    dataset['type'] = 'bar'
                    dataset['backgroundColor'] = config['color'] + '80'
                    dataset['borderColor'] = config['color']
                    dataset['borderWidth'] = 1
                elif chart_style == 'area':
                    dataset['fill'] = True
                    dataset['backgroundColor'] = config['color'] + '40'
                else:  # line
                    dataset['fill'] = False
                    dataset['pointBackgroundColor'] = config['color']
                    dataset['pointBorderColor'] = '#fff'
                    dataset['pointBorderWidth'] = 2

                datasets.append(dataset)

        return {
            'labels': labels,
            'datasets': datasets
        }

    def generate_mock_time_series(self, start_date, end_date):
        """Генерация тестовых временных рядов"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end - start).days + 1

        time_series = []
        current = start

        for i in range(days_diff * 24):  # Почасовые данные
            time_series.append({
                'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                'distance': round(random.uniform(5, 50), 2),
                'fuel_consumption': round(random.uniform(2, 15), 2),
                'max_speed': round(random.uniform(30, 90), 2),
                'engine_hours': round(random.uniform(0.5, 2.5), 2),
                'fuel_level': round(random.uniform(100, 500), 2),
                'total_fuel_volume': round(random.uniform(200, 600), 2),
            })
            current += timedelta(hours=1)

        return time_series

    def generate_mock_chart_data(self, start_date, end_date, metrics, chart_style):
        """Генерация тестовых данных для графиков"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end - start).days + 1

        labels = [((start + timedelta(days=i)).strftime('%d.%m.%Y')) for i in range(days_diff)]

        metrics_config = {
            'distance': {'label': 'Пробег', 'unit': 'км', 'color': '#27ae60', 'min': 100, 'max': 400},
            'fuel_consumption': {'label': 'Расход топлива', 'unit': 'л', 'color': '#e74c3c', 'min': 20, 'max': 60},
            'max_speed': {'label': 'Скорость', 'unit': 'км/ч', 'color': '#3498db', 'min': 30, 'max': 90},
            'engine_hours': {'label': 'Моточасы', 'unit': 'ч', 'color': '#f39c12', 'min': 4, 'max': 12},
            'fuel_level': {'label': 'Уровень топлива', 'unit': 'л', 'color': '#9b59b6', 'min': 100, 'max': 500},
            'total_fuel_volume': {'label': 'Общий объем топлива', 'unit': 'л', 'color': '#e67e22', 'min': 200,
                                  'max': 600},
        }

        datasets = []
        for metric in metrics:
            if metric in metrics_config:
                config = metrics_config[metric]
                data = [round(random.uniform(config['min'], config['max']), 2) for _ in range(days_diff)]

                dataset = {
                    'label': f"{config['label']} ({config['unit']})",
                    'data': data,
                    'borderColor': config['color'],
                    'backgroundColor': config['color'] + '20',
                    'tension': 0.4,
                }

                # Настройки в зависимости от стиля графика
                if chart_style == 'bar':
                    dataset['type'] = 'bar'
                    dataset['backgroundColor'] = config['color'] + '80'
                    dataset['borderColor'] = config['color']
                    dataset['borderWidth'] = 1
                elif chart_style == 'area':
                    dataset['fill'] = True
                    dataset['backgroundColor'] = config['color'] + '40'
                else:  # line
                    dataset['fill'] = False
                    dataset['pointBackgroundColor'] = config['color']
                    dataset['pointBorderColor'] = '#fff'
                    dataset['pointBorderWidth'] = 2

                datasets.append(dataset)

        return {
            'labels': labels,
            'datasets': datasets
        }


class VehicleHistoricalDataAPI(APIView):
    permission_classes = [AllowAny]  # Временно отключаем аутентификацию

    def get(self, request):
        """API для детальных исторических данных"""
        try:
            return Response({
                'success': True,
                'historical_data': {
                    'trips_count': 24,
                    'total_period': '7 дней',
                    'note': 'Исторические данные о поездках'
                }
            })

        except Exception as e:
            logger.error(f"Historical data API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)