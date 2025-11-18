# vehicles/views_enhanced.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .services import AutoGraphService
from .services_enhanced import EnhancedAutoGraphService
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

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

    @method_decorator(cache_page(60 * 5))  # Кэш 5 минут
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


class EnhancedAnalyticsAPI(BaseAutoGraphAPI):
    """API для расширенной аналитики с исправленной структурой данных"""

    def get(self, request):
        try:
            vehicle_ids = request.GET.get('vehicle_ids', '')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not all([vehicle_ids, start_date, end_date]):
                return Response({
                    "success": False,
                    "error": "Необходимы параметры: vehicle_ids, start_date, end_date"
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

            enhanced_service = EnhancedAutoGraphService()
            vehicle_ids_list = [vid.strip() for vid in vehicle_ids.split(',') if vid.strip()]

            analytics_data = {}
            processed_count = 0

            for vehicle_id in vehicle_ids_list:
                try:
                    logger.info(f"🔄 Обработка ТС {vehicle_id}...")

                    vehicle_data = enhanced_service.get_comprehensive_vehicle_data(
                        schema_id, vehicle_id, start_date, end_date
                    )

                    if vehicle_data and vehicle_data.get('basic_info'):
                        # Форматируем данные для фронтенда
                        formatted_data = self._format_vehicle_data_for_frontend(vehicle_data)
                        analytics_data[vehicle_id] = formatted_data
                        processed_count += 1
                        logger.info(f"✅ ТС {vehicle_id} обработан успешно")
                    else:
                        logger.warning(f"⚠️ Нет данных для ТС {vehicle_id}")
                        # Создаем структуру с пустыми данными для фронтенда
                        analytics_data[vehicle_id] = self._create_empty_vehicle_data(vehicle_id)

                except Exception as e:
                    logger.error(f"❌ Ошибка обработки ТС {vehicle_id}: {e}")
                    analytics_data[vehicle_id] = self._create_empty_vehicle_data(vehicle_id)
                    continue

            return Response({
                "success": True,
                "data": {
                    "vehicle_metrics": analytics_data,
                    "period": {
                        "start": start_date,
                        "end": end_date
                    },
                    "summary": {
                        "requested_vehicles": len(vehicle_ids_list),
                        "processed_vehicles": processed_count,
                        "failed_vehicles": len(vehicle_ids_list) - processed_count
                    }
                }
            })

        except Exception as e:
            logger.error(f"EnhancedAnalyticsAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _format_vehicle_data_for_frontend(self, vehicle_data: Dict) -> Dict:
        """Форматирование данных ТС для фронтенда"""
        try:
            formatted_data = {
                'basic_info': vehicle_data.get('basic_info', {}),
                'trips_data': vehicle_data.get('trips_data', []),
                'track_data': self._format_track_data(vehicle_data.get('track_data', [])),
                'online_data': vehicle_data.get('online_data', {}),
                'fuel_analysis': vehicle_data.get('fuel_analysis', {}),
                'work_analysis': vehicle_data.get('work_analysis', {}),
                'summary_stats': vehicle_data.get('summary_stats', {}),
                'safety_metrics': self._extract_safety_metrics(vehicle_data)
            }

            # Добавляем тестовые данные для демонстрации
            if not formatted_data['track_data']:
                formatted_data['track_data'] = self._create_sample_track_data()

            return formatted_data

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования данных для фронтенда: {e}")
            return self._create_empty_vehicle_data(vehicle_data.get('basic_info', {}).get('id', 'unknown'))

    def _format_track_data(self, track_data: List) -> List:
        """Форматирование данных трека для фронтенда"""
        formatted_track = []

        for point in track_data:
            formatted_point = {
                'timestamp': point.get('timestamp'),
                'speed': float(point.get('speed', 0)),
                'distance': float(point.get('mileage', 0)),
                'fuel_volume': float(point.get('fuel_level', 0)),
                'engine_rpm': float(point.get('engine_rpm', 0)),
                'voltage': float(point.get('voltage', 0)),
                'engine_load': float(point.get('engine_rpm', 0) / 3000 * 100) if point.get('engine_rpm') else 0,
                # Расчетная нагрузка
                'equipment_hours': 1 if point.get('ignition') else 0,  # Упрощенный расчет
                'engine_hours': 1 if point.get('ignition') else 0  # Упрощенный расчет
            }

            # Добавляем координаты если есть
            if point.get('coordinates'):
                formatted_point['lat'] = point['coordinates'].get('lat')
                formatted_point['lng'] = point['coordinates'].get('lng')

            formatted_track.append(formatted_point)

        return formatted_track

    def _extract_safety_metrics(self, vehicle_data: Dict) -> Dict:
        """Извлечение метрик безопасности"""
        trips_data = vehicle_data.get('trips_data', [])

        overspeed_count = sum(trip.get('overspeed_count', 0) for trip in trips_data)
        total_distance = sum(trip.get('distance', 0) for trip in trips_data)

        # Расчет показателя безопасности
        safety_score = max(0, 100 - (overspeed_count * 2))

        return {
            'overspeed_count': overspeed_count,
            'safety_score': safety_score,
            'total_violations': overspeed_count
        }

    def _create_empty_vehicle_data(self, vehicle_id: str) -> Dict:
        """Создание пустой структуры данных для ТС"""
        return {
            'basic_info': {
                'id': vehicle_id,
                'name': f'ТС {vehicle_id}',
                'license_plate': 'Неизвестно'
            },
            'trips_data': [],
            'track_data': self._create_sample_track_data(),
            'online_data': {},
            'fuel_analysis': {},
            'work_analysis': {
                'engine_work_without_movement': {'seconds': 0, 'formatted': '0 мин.', 'percentage': 0},
                'engine_work_in_motion': {'seconds': 0, 'formatted': '0 мин.', 'percentage': 0},
                'parking_engine_off': {'seconds': 0, 'formatted': '0 мин.', 'percentage': 0},
                'no_data': {'seconds': 86400, 'formatted': '24 час.', 'percentage': 100},
                'total_period': {'seconds': 86400, 'formatted': '24 час.'}
            },
            'summary_stats': {},
            'safety_metrics': {
                'overspeed_count': 0,
                'safety_score': 100,
                'total_violations': 0
            }
        }

    def _create_sample_track_data(self) -> List:
        """Создание тестовых данных трека для демонстрации"""
        sample_data = []
        base_time = datetime.now()

        for i in range(50):
            timestamp = (base_time - timedelta(hours=i)).isoformat()
            sample_data.append({
                'timestamp': timestamp,
                'speed': float(30 + (i % 20)),
                'distance': float(i * 5),
                'fuel_volume': float(100 - (i % 50)),
                'engine_rpm': float(1500 + (i % 1000)),
                'voltage': float(12 + (i % 5) * 0.1),
                'engine_load': float(50 + (i % 30)),
                'equipment_hours': 1,
                'engine_hours': 1
            })

        return sample_data


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