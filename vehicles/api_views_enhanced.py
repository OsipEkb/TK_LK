from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .services import AutoGraphService
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaseAutoGraphAPI(APIView):
    """Базовый класс для AutoGRAPH API"""

    def __init__(self):
        super().__init__()
        self.service = AutoGraphService()

    def _authenticate(self) -> bool:
        """Аутентификация с кэшированием"""
        return self.service.login()

    def _get_schema_id(self) -> Optional[str]:
        """Получение ID схемы"""
        schemas = self.service.get_schemas()
        return schemas[0].get('ID') if schemas else None


class VehicleListAPI(BaseAutoGraphAPI):
    """API для получения списка ТС"""

    @method_decorator(cache_page(60))  # Кэш 1 минута
    def get(self, request):
        try:
            if not self._authenticate():
                return Response({
                    "success": False,
                    "error": "Ошибка аутентификации"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            schema_id = self._get_schema_id()
            if not schema_id:
                return Response({
                    "success": False,
                    "error": "Нет доступных схем"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            vehicles_data = self.service.get_vehicles(schema_id)

            if not vehicles_data or 'Items' not in vehicles_data:
                return Response({
                    "success": False,
                    "error": "Нет данных о ТС"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Форматируем данные
            formatted_vehicles = []
            for vehicle in vehicles_data['Items']:
                formatted_vehicles.append({
                    'id': vehicle.get('ID'),
                    'name': vehicle.get('Name', 'Unknown'),
                    'license_plate': self.service.extract_license_plate(vehicle),
                    'serial': vehicle.get('Serial'),
                    'schema_id': schema_id
                })

            return Response({
                "success": True,
                "data": {
                    "vehicles": formatted_vehicles,
                    "total_count": len(formatted_vehicles)
                }
            })

        except Exception as e:
            logger.error(f"VehicleListAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VehicleStatisticsAPI(BaseAutoGraphAPI):
    """API для получения статистики ТС"""

    def get(self, request):
        try:
            vehicle_id = request.GET.get('vehicle_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not all([vehicle_id, start_date, end_date]):
                return Response({
                    "success": False,
                    "error": "Необходимы параметры: vehicle_id, start_date, end_date"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not self._authenticate():
                return Response({
                    "success": False,
                    "error": "Ошибка аутентификации"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            schema_id = self._get_schema_id()
            if not schema_id:
                return Response({
                    "success": False,
                    "error": "Нет доступных схем"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Форматируем даты
            start_fmt = self.service.format_date_for_api(start_date, is_start=True)
            end_fmt = self.service.format_date_for_api(end_date, is_start=False)

            # Получаем данные рейсов
            trips_data = self.service.get_trips_total(schema_id, vehicle_id, start_fmt, end_fmt)

            if not trips_data or vehicle_id not in trips_data:
                return Response({
                    "success": False,
                    "error": "Нет данных за указанный период"
                }, status=status.HTTP_404_NOT_FOUND)

            vehicle_data = trips_data[vehicle_id]
            trips = vehicle_data.get('Trips', [])

            # Обрабатываем данные
            statistics = self._process_trips_data(trips, vehicle_data)

            return Response({
                "success": True,
                "data": statistics
            })

        except Exception as e:
            logger.error(f"VehicleStatisticsAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_trips_data(self, trips: List, vehicle_data: Dict) -> Dict:
        """Обработка данных рейсов"""
        if not trips:
            return {
                "vehicle_info": {
                    "name": vehicle_data.get('Name', 'Unknown'),
                    "license_plate": vehicle_data.get('VRN', 'Unknown')
                },
                "summary": {},
                "trips": []
            }

        # Суммируем данные по всем рейсам
        total_stats = {
            'total_distance': 0,
            'total_fuel_consumption': 0,
            'total_duration': 0,
            'max_speed': 0,
            'trips_count': len(trips)
        }

        detailed_trips = []

        for trip in trips:
            trip_total = trip.get('Total', {})

            # Основные показатели
            distance = trip_total.get('TotalDistance', 0)
            fuel = trip_total.get('Engine1FuelConsum', 0)
            max_speed = trip_total.get('MaxSpeed', 0)

            total_stats['total_distance'] += distance
            total_stats['total_fuel_consumption'] += fuel
            total_stats['max_speed'] = max(total_stats['max_speed'], max_speed)

            # Детали рейса
            detailed_trips.append({
                'start_time': trip.get('SD'),
                'end_time': trip.get('ED'),
                'distance': round(distance, 2),
                'fuel_consumption': round(fuel, 2),
                'max_speed': round(max_speed, 2),
                'start_location': trip_total.get('FirstLocation', ''),
                'end_location': trip_total.get('LastLocation', '')
            })

        # Рассчитываем средние показатели
        if total_stats['total_distance'] > 0:
            total_stats['fuel_efficiency'] = round(
                (total_stats['total_fuel_consumption'] / total_stats['total_distance']) * 100, 2
            )

        return {
            "vehicle_info": {
                "name": vehicle_data.get('Name', 'Unknown'),
                "license_plate": vehicle_data.get('VRN', 'Unknown')
            },
            "summary": {
                **total_stats,
                "total_distance": round(total_stats['total_distance'], 2),
                "total_fuel_consumption": round(total_stats['total_fuel_consumption'], 2)
            },
            "trips": detailed_trips
        }


class VehicleOnlineStatusAPI(BaseAutoGraphAPI):
    """API для получения онлайн статуса ТС"""

    @method_decorator(cache_page(30))  # Кэш 30 секунд
    def get(self, request):
        try:
            if not self._authenticate():
                return Response({
                    "success": False,
                    "error": "Ошибка аутентификации"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            schema_id = self._get_schema_id()
            if not schema_id:
                return Response({
                    "success": False,
                    "error": "Нет доступных схем"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            online_data = self.service.get_online_info_all(schema_id)

            if not online_data:
                return Response({
                    "success": False,
                    "error": "Нет онлайн данных"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Группируем по статусам
            status_groups = {
                'moving': [],
                'parking': [],
                'offline': []
            }

            for vehicle_id, data in online_data.items():
                vehicle_status = self._get_vehicle_status(data)

                vehicle_info = {
                    'id': vehicle_id,
                    'name': data.get('Name', 'Unknown'),
                    'license_plate': data.get('VRN', 'Unknown'),
                    'location': data.get('Total', {}).get('CurrLocation', 'Не определено'),
                    'last_update': data.get('_LastDataLocal', ''),
                    'speed': data.get('Total', {}).get('Speed Last', 0)
                }

                status_groups[vehicle_status].append(vehicle_info)

            return Response({
                "success": True,
                "data": {
                    "total_vehicles": len(online_data),
                    "status_groups": status_groups
                }
            })

        except Exception as e:
            logger.error(f"VehicleOnlineStatusAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_vehicle_status(self, vehicle_data: Dict) -> str:
        """Определение статуса ТС"""
        motion = vehicle_data.get('Total', {}).get('Motion Last', 1)
        speed = vehicle_data.get('Total', {}).get('Speed Last', 0)

        if motion == 2 or speed > 0:
            return 'moving'
        elif motion == 1:
            return 'parking'
        else:
            return 'offline'


class SystemHealthAPI(BaseAutoGraphAPI):
    """API для проверки здоровья системы"""

    def get(self, request):
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "services": {}
            }

            # Проверяем аутентификацию
            auth_success = self.service.login()
            health_status["services"]["authentication"] = "healthy" if auth_success else "unhealthy"

            if auth_success:
                # Проверяем доступность данных
                schemas = self.service.get_schemas()
                health_status["services"]["data_availability"] = "healthy" if schemas else "unhealthy"
                health_status["schemas_count"] = len(schemas) if schemas else 0

            return Response({
                "success": True,
                "health": health_status
            })

        except Exception as e:
            logger.error(f"SystemHealthAPI error: {e}")
            return Response({
                "success": False,
                "health": {
                    "timestamp": datetime.now().isoformat(),
                    "status": "unhealthy",
                    "error": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)