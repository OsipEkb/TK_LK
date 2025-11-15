# vehicles/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from vehicles.services import AutoGraphService
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class VehiclesListAPI(APIView):
    permission_classes = [IsAuthenticated]

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
                            vehicle_info = {
                                'id': vehicle.get('ID'),
                                'name': vehicle.get('Name', 'Unknown'),
                                'license_plate': self.extract_license_plate(vehicle),
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

    def extract_license_plate(self, vehicle_data):
        """Извлечение госномера"""
        try:
            properties = vehicle_data.get('properties', [])
            for prop in properties:
                if prop.get('name') in ['LicensePlate', 'Госномер', 'Номер', 'VehicleRegNumber']:
                    value = prop.get('value', '')
                    if value:
                        return value

            name = vehicle_data.get('Name', '')
            return name[:15]
        except:
            return vehicle_data.get('Name', 'Unknown')[:15]

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET метод для получения статистики по КОНКРЕТНОМУ ТС"""
        try:
            # Получаем параметры из GET запроса
            vehicle_id = request.GET.get('vehicle_id')
            schema_id = request.GET.get('schema_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            time_step = request.GET.get('time_step', 'hour')

            logger.info(f"🔄 GET Statistics for SPECIFIC vehicle: {vehicle_id} from {start_date} to {end_date}")

            if not all([vehicle_id, schema_id, start_date, end_date]):
                return Response({
                    'success': False,
                    'error': 'Отсутствуют обязательные параметры: vehicle_id, schema_id, start_date, end_date'
                }, status=400)

            # Получаем информацию о выбранном ТС
            vehicle_info = self.get_vehicle_info(vehicle_id)
            if not vehicle_info:
                return Response({
                    'success': False,
                    'error': f'ТС с ID {vehicle_id} не найдено'
                }, status=404)

            # Генерируем статистику ТОЛЬКО для выбранного ТС
            statistics_data = self.generate_vehicle_specific_statistics(
                vehicle_info, start_date, end_date, time_step
            )

            return Response({
                'success': True,
                'statistics': statistics_data,
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'step': time_step
                },
                'vehicle_id': vehicle_id,
                'vehicle_info': vehicle_info
            })

        except Exception as e:
            logger.error(f"Vehicle statistics API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)

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
            },
            'mock-4': {
                'id': 'mock-4',
                'name': '716 Freightliner',
                'license_plate': 'Н 716 ВК 186',
                'serial': '379847',
                'type': 'Грузовой',
                'model': 'Freightliner'
            },
            'mock-5': {
                'id': 'mock-5',
                'name': '031 Freightliner',
                'license_plate': 'Н 031 ВК 186',
                'serial': '380151',
                'type': 'Грузовой',
                'model': 'Freightliner'
            }
        }

        return vehicles_data.get(vehicle_id)

    def generate_vehicle_specific_statistics(self, vehicle_info, start_date, end_date, time_step):
        """Генерация статистики для КОНКРЕТНОГО ТС"""
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
        }

        # Генерация временных рядов для конкретного ТС
        time_series = self.generate_vehicle_time_series(vehicle_info, start, end, time_step, vehicle_hash)

        return {
            'summary': base_stats,
            'time_series': time_series,
            'vehicle_id': vehicle_info['id'],
            'vehicle_name': vehicle_info['name'],
            'data_source': 'vehicle_specific'
        }

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
        intervals = []
        current = start

        # Уникальные коэффициенты для каждого ТС
        distance_factor = 0.8 + (vehicle_hash % 40) / 100
        fuel_factor = 0.7 + (vehicle_hash % 50) / 100
        speed_factor = 0.9 + (vehicle_hash % 20) / 100

        while current <= end:
            # Генерация данных с учетом характеристик ТС
            day_data = self.generate_vehicle_day_data(current, vehicle_hash, distance_factor, fuel_factor, speed_factor)

            interval_data = {
                'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                'distance': day_data['distance'],
                'fuel_consumption': day_data['fuel'],
                'engine_hours': day_data['hours'],
                'move_duration': day_data['move_duration'],
                'max_speed': day_data['speed'],
            }
            intervals.append(interval_data)

            if time_step == 'hour':
                current += timedelta(hours=1)
            elif time_step == 'day':
                current += timedelta(days=1)
            elif time_step == 'week':
                current += timedelta(weeks=1)

        return intervals

    def generate_vehicle_day_data(self, date, vehicle_hash, distance_factor, fuel_factor, speed_factor):
        """Генерация дневных данных для конкретного ТС"""
        day_of_week = date.weekday()
        is_weekend = day_of_week >= 5

        # Базовые значения с учетом характеристик ТС
        if is_weekend:
            base_distance = 40 * distance_factor
            base_fuel = 15 * fuel_factor
            base_speed = 35 * speed_factor
        else:
            base_distance = 100 * distance_factor
            base_fuel = 35 * fuel_factor
            base_speed = 55 * speed_factor

        # Добавляем случайные вариации
        variation = random.uniform(-0.15, 0.15)

        return {
            'distance': round(base_distance * (1 + variation), 2),
            'fuel': round(base_fuel * (1 + variation), 2),
            'speed': round(base_speed * (1 + variation * 0.5), 2),
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
        return f"{hours:02d}:{minutes:02d}:00"

    def generate_daily_move_duration(self, vehicle_hash, is_weekend):
        """Генерация времени в движении"""
        if is_weekend:
            hours = 1 + (vehicle_hash % 2)
        else:
            hours = 3 + (vehicle_hash % 4)
        minutes = random.randint(0, 59)
        return f"{hours:02d}:{minutes:02d}:00"


class VehicleChartDataAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """API для данных графиков"""
        try:
            chart_type = request.GET.get('chart_type', 'fuel')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': 'Отсутствуют start_date или end_date'
                }, status=400)

            chart_data = self.generate_mock_chart_data(chart_type, start_date, end_date)

            return Response({
                'success': True,
                'chart_data': chart_data,
                'chart_type': chart_type
            })

        except Exception as e:
            logger.error(f"Chart data API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)

    def generate_mock_chart_data(self, chart_type, start_date, end_date):
        """Генерация данных для графиков"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end - start).days + 1

        labels = [((start + timedelta(days=i)).strftime('%d.%m.%Y')) for i in range(days_diff)]

        configs = {
            'fuel': {'label': 'Расход топлива (л)', 'color': '#e74c3c', 'min': 20, 'max': 60},
            'distance': {'label': 'Пробег (км)', 'color': '#27ae60', 'min': 100, 'max': 400},
            'speed': {'label': 'Скорость (км/ч)', 'color': '#3498db', 'min': 30, 'max': 90},
            'hours': {'label': 'Время работы (ч)', 'color': '#f39c12', 'min': 4, 'max': 12},
        }

        config = configs.get(chart_type, configs['fuel'])
        data = [round(random.uniform(config['min'], config['max']), 2) for _ in range(days_diff)]

        return {
            'labels': labels,
            'datasets': [{
                'label': config['label'],
                'data': data,
                'borderColor': config['color'],
                'backgroundColor': config['color'] + '20',
                'tension': 0.4,
                'fill': True
            }]
        }


class VehicleHistoricalDataAPI(APIView):
    permission_classes = [IsAuthenticated]

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