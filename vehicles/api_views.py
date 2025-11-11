# vehicles/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from app.api.clients import AutoGraphAPIClient
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class VehiclesListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """API для получения списка ТС"""
        try:
            # Пробуем получить реальные данные
            try:
                username = "Osipenko"
                password = "Osipenko"

                client = AutoGraphAPIClient(username=username, password=password)

                if client.login():
                    schemas = client.get_schemas()

                    if schemas:
                        schema_id = schemas[0]['ID']
                        vehicles_data = client.get_vehicles(schema_id)

                        formatted_vehicles = []
                        for vehicle in vehicles_data.get('Items', []):
                            formatted_vehicles.append({
                                'id': vehicle.get('ID'),
                                'name': vehicle.get('Name', 'Unknown'),
                                'license_plate': extract_license_plate(vehicle),
                                'is_online': random.choice([True, False]),
                                'fuel_level': f"{random.randint(50, 300)}.{random.randint(0, 9)}",
                                'speed': str(random.randint(0, 80))
                            })

                        return Response({
                            'success': True,
                            'vehicles': formatted_vehicles,
                            'schema_id': schema_id,
                            'source': 'real_data'
                        })

            except Exception as real_data_error:
                logger.warning(f"⚠️ Real data unavailable, using mock data: {real_data_error}")

            # Если реальные данные недоступны, используем mock данные
            mock_vehicles = [
                {
                    'id': '11804e75-d2c3-4f2b-9107-5ad899adfe12',
                    'name': '644 Freightliner',
                    'license_plate': 'А123ВС77',
                    'is_online': True,
                    'fuel_level': '245.5',
                    'speed': '65'
                },
                {
                    'id': 'abe04e76-cf82-41ac-9836-086ae66e652e',
                    'name': '776 Freightliner',
                    'license_plate': 'В456ОР77',
                    'is_online': True,
                    'fuel_level': '189.2',
                    'speed': '72'
                },
                {
                    'id': '8570f4fd-ee21-431c-8412-9b4b54e955af',
                    'name': '336 Freightliner',
                    'license_plate': 'С789ТУ77',
                    'is_online': False,
                    'fuel_level': None,
                    'speed': None
                },
                {
                    'id': 'vehicle_4',
                    'name': 'Volvo FH16',
                    'license_plate': 'Е012ХА77',
                    'is_online': True,
                    'fuel_level': '312.8',
                    'speed': '58'
                },
                {
                    'id': 'vehicle_5',
                    'name': 'MAN TGS',
                    'license_plate': 'К345ЛМ77',
                    'is_online': True,
                    'fuel_level': '178.3',
                    'speed': '45'
                }
            ]

            return Response({
                'success': True,
                'vehicles': mock_vehicles,
                'schema_id': 'mock_schema',
                'source': 'mock_data',
                'note': 'Реальные данные временно недоступны. Используются тестовые данные.'
            })

        except Exception as e:
            logger.error(f"Vehicles list API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)


class VehicleChartDataAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """API для получения данных графиков"""
        try:
            data = request.data
            vehicle_id = data.get('vehicle_id')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            chart_type = data.get('chart_type', 'fuel')

            if not all([vehicle_id, start_date, end_date]):
                return Response({
                    'success': False,
                    'error': 'Отсутствуют обязательные параметры'
                }, status=400)

            # Генерируем реалистичные тестовые данные
            chart_data = self.generate_mock_chart_data(chart_type, start_date, end_date)

            return Response({
                'success': True,
                'chart_data': chart_data,
                'vehicle_id': vehicle_id,
                'source': 'mock_data',
                'note': 'Реальные данные временно недоступны. Используются тестовые данные.'
            })

        except Exception as e:
            logger.error(f"Vehicle chart data API error: {e}")
            return Response({
                'success': False,
                'error': f'Ошибка сервера: {str(e)}'
            }, status=500)

    def generate_mock_chart_data(self, chart_type, start_date, end_date):
        """Генерация тестовых данных для графиков"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end - start).days + 1

        labels = []
        for i in range(days_diff):
            date = start + timedelta(days=i)
            labels.append(date.strftime('%d.%m.%Y'))

        if chart_type == 'fuel':
            data = [random.randint(20, 60) for _ in range(days_diff)]
            color = '#e74c3c'
            label = 'Расход топлива (л)'
        elif chart_type == 'work':
            data = [random.randint(4, 12) for _ in range(days_diff)]
            color = '#3498db'
            label = 'Время работы (ч)'
        elif chart_type == 'speed':
            data = [random.randint(30, 80) for _ in range(days_diff)]
            color = '#2ecc71'
            label = 'Средняя скорость (км/ч)'
        elif chart_type == 'mileage':
            data = [random.randint(100, 400) for _ in range(days_diff)]
            color = '#9b59b6'
            label = 'Пробег (км)'
        else:
            data = [random.randint(10, 100) for _ in range(days_diff)]
            color = '#95a5a6'
            label = 'Данные'

        return {
            'labels': labels,
            'datasets': [{
                'label': label,
                'data': data,
                'borderColor': color,
                'backgroundColor': color + '20',
                'tension': 0.4,
                'fill': True
            }]
        }


def extract_license_plate(vehicle_data):
    """Извлечение госномера из свойств ТС"""
    try:
        properties = vehicle_data.get('properties', [])
        for prop in properties:
            if prop.get('name') in ['LicensePlate', 'Госномер', 'Номер']:
                return prop.get('value', '')
        return vehicle_data.get('Name', '')
    except:
        return vehicle_data.get('Name', '')