from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from vehicles.services import AutoGraphService
from vehicles.services_enhanced import EnhancedAutoGraphService
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ReportsVehicleListAPI(APIView):
    """API для получения списка ТС для страницы отчетов"""

    def get(self, request):
        try:
            service = AutoGraphService()

            if not service.login():
                return Response({
                    "success": False,
                    "error": "Ошибка аутентификации"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            schemas = service.get_schemas()
            if not schemas:
                return Response({
                    "success": False,
                    "error": "Нет доступных схем"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            schema_id = schemas[0].get('ID')
            vehicles_data = service.get_vehicles(schema_id)

            if not vehicles_data or 'Items' not in vehicles_data:
                return Response({
                    "success": False,
                    "error": "Нет данных о ТС"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Форматируем данные для фронтенда
            formatted_vehicles = []
            for vehicle in vehicles_data['Items']:
                license_plate = service.extract_license_plate(vehicle)

                formatted_vehicles.append({
                    'id': vehicle.get('ID'),
                    'name': vehicle.get('Name', 'Unknown'),
                    'license_plate': license_plate,
                    'serial': vehicle.get('Serial'),
                    'schema_id': schema_id,
                    'properties': vehicle.get('Properties', [])
                })

            return Response({
                "success": True,
                "data": {
                    "vehicles": formatted_vehicles,
                    "schema_name": schemas[0].get('Name', 'Основная схема'),
                    "total_count": len(formatted_vehicles)
                }
            })

        except Exception as e:
            logger.error(f"ReportsVehicleListAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(login_required, name='dispatch')
class GenerateReportAPI(View):
    """API для генерации отчетов"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            report_type = data.get('report_type')
            vehicle_ids = data.get('vehicle_ids', [])
            start_date = data.get('start_date')
            end_date = data.get('end_date')

            if not report_type:
                return JsonResponse({
                    "success": False,
                    "error": "Не указан тип отчета"
                })

            if not vehicle_ids:
                return JsonResponse({
                    "success": False,
                    "error": "Не выбраны транспортные средства"
                })

            # Генерируем отчет
            report_data = self._generate_report(
                report_type, vehicle_ids, start_date, end_date
            )

            return JsonResponse({
                "success": True,
                "data": report_data,
                "report_info": {
                    "type": report_type,
                    "vehicle_count": len(vehicle_ids),
                    "period": f"{start_date} - {end_date}"
                }
            })

        except Exception as e:
            logger.error(f"GenerateReportAPI error: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Ошибка генерации отчета: {str(e)}"
            })

    def _generate_report(self, report_type, vehicle_ids, start_date, end_date):
        """Генерация данных отчета"""

        # Используем существующие сервисы
        service = AutoGraphService()
        enhanced_service = EnhancedAutoGraphService()

        if not service.login():
            return {"error": "Ошибка аутентификации"}

        schemas = service.get_schemas()
        if not schemas:
            return {"error": "Нет доступных схем"}

        schema_id = schemas[0].get('ID')

        report_data = {
            "summary": {},
            "details": [],
            "vehicles": []
        }

        # Собираем данные по каждому ТС
        for vehicle_id in vehicle_ids:
            try:
                # Получаем комплексные данные для ТС
                comprehensive_data = enhanced_service.get_comprehensive_vehicle_data(
                    schema_id, vehicle_id, start_date, end_date
                )

                if comprehensive_data and comprehensive_data.get('basic_info'):
                    vehicle_report = self._format_vehicle_report(
                        report_type, comprehensive_data, vehicle_id
                    )
                    report_data["details"].append(vehicle_report)
                    report_data["vehicles"].append({
                        'id': vehicle_id,
                        'name': comprehensive_data['basic_info'].get('name', 'Unknown'),
                        'license_plate': comprehensive_data['basic_info'].get('license_plate', 'Unknown')
                    })

            except Exception as e:
                logger.error(f"Error processing vehicle {vehicle_id}: {e}")
                continue

        # Рассчитываем сводную статистику
        report_data["summary"] = self._calculate_summary_stats(report_data["details"], report_type)

        return report_data

    def _format_vehicle_report(self, report_type, comprehensive_data, vehicle_id):
        """Форматирование данных отчета для конкретного ТС"""

        summary_stats = comprehensive_data.get('summary_stats', {})
        fuel_analysis = comprehensive_data.get('fuel_analysis', {})
        work_analysis = comprehensive_data.get('work_analysis', {})
        trips_data = comprehensive_data.get('trips_data', [])
        track_data = comprehensive_data.get('track_data', [])

        base_data = {
            'vehicleName': comprehensive_data['basic_info'].get('name', 'Unknown'),
            'licensePlate': comprehensive_data['basic_info'].get('license_plate', 'Unknown'),
        }

        # Движение
        if report_type == 'movement':
            return {
                **base_data,
                'group': 'Основная группа',
                'date': datetime.now().strftime('%d.%m.%Y'),
                'distance': summary_stats.get('total_distance', 0),
                'avgSpeed': self._calculate_average_speed(trips_data),
                'maxSpeed': self._calculate_max_speed(trips_data),
                'moveTime': summary_stats.get('total_engine_hours', '00:00:00'),
                'engineTime': summary_stats.get('total_engine_hours', '00:00:00')
            }

        # Заправки
        elif report_type == 'refueling':
            return {
                **base_data,
                'date': datetime.now().strftime('%d.%m.%Y'),
                'startVolume': 0,
                'endVolume': self._get_last_fuel_level(track_data),
                'actualConsumption': summary_stats.get('total_fuel_consumption', 0),
                'refillVolume': fuel_analysis.get('total_refills_volume', 0),
                'drainVolume': 0,
                'consumptionPer100km': summary_stats.get('avg_fuel_efficiency', 0)
            }

        # Нарушения
        elif report_type == 'violations':
            max_speed = self._calculate_max_speed(trips_data)
            overspeed_count = len([t for t in trips_data if t.get('max_speed', 0) > 90])

            return {
                **base_data,
                'datetime': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'violationType': 'Превышение скорости' if max_speed > 90 else 'Нет нарушений',
                'parameters': f'Макс. скорость: {max_speed} км/ч',
                'location': self._get_last_location(track_data),
                'duration': '00:00:00'
            }

        # Сводный отчет
        elif report_type == 'summary':
            return {
                **base_data,
                'distance': summary_stats.get('total_distance', 0),
                'workTime': summary_stats.get('total_engine_hours', '00:00:00'),
                'fuelConsumption': summary_stats.get('total_fuel_consumption', 0),
                'avgSpeed': self._calculate_average_speed(trips_data),
                'violationsCount': len([t for t in trips_data if t.get('max_speed', 0) > 90])
            }

        # Журнал
        elif report_type == 'journal':
            return {
                **base_data,
                'datetime': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'event': 'Анализ данных',
                'location': self._get_last_location(track_data),
                'parameters': f'Пробег: {summary_stats.get("total_distance", 0)} км',
                'status': 'Завершено'
            }

        # Посменный отчет
        elif report_type == 'shift':
            return {
                **base_data,
                'shift': 'Смена 1',
                'date': datetime.now().strftime('%d.%m.%Y'),
                'driver': 'Водитель не назначен',
                'distance': summary_stats.get('total_distance', 0),
                'workTime': summary_stats.get('total_engine_hours', '00:00:00'),
                'fuelConsumption': summary_stats.get('total_fuel_consumption', 0)
            }

        # Работа группы
        elif report_type == 'group':
            return {
                **base_data,
                'group': 'Основная группа',
                'distance': summary_stats.get('total_distance', 0),
                'workTime': summary_stats.get('total_engine_hours', '00:00:00'),
                'fuelConsumption': summary_stats.get('total_fuel_consumption', 0),
                'efficiency': summary_stats.get('avg_fuel_efficiency', 0)
            }

        # События
        elif report_type == 'events':
            return {
                **base_data,
                'datetime': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'eventType': 'Анализ данных',
                'description': f'Пробег: {summary_stats.get("total_distance", 0)} км',
                'location': self._get_last_location(track_data),
                'duration': '01:00:00'
            }

        # Статистика
        elif report_type == 'statistics':
            return {
                **base_data,
                'period': 'День',
                'distance': summary_stats.get('total_distance', 0),
                'moveTime': summary_stats.get('total_engine_hours', '00:00:00'),
                'idleTime': self._calculate_idle_time(work_analysis),
                'fuelConsumption': summary_stats.get('total_fuel_consumption', 0),
                'efficiency': summary_stats.get('avg_fuel_efficiency', 0)
            }

        # Стоянки
        elif report_type == 'parking':
            return {
                **base_data,
                'parkingStart': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'parkingEnd': (datetime.now() + timedelta(hours=2)).strftime('%d.%m.%Y %H:%M'),
                'duration': '02:00:00',
                'location': self._get_last_location(track_data),
                'reason': 'Плановый перерыв'
            }

        else:
            return base_data

    def _calculate_summary_stats(self, details, report_type):
        """Расчет сводной статистики"""
        if not details:
            return {}

        if report_type == 'movement':
            return {
                'totalVehicles': len(details),
                'totalDistance': sum(item.get('distance', 0) for item in details),
                'avgSpeed': sum(item.get('avgSpeed', 0) for item in details) / len(details),
                'totalEngineHours': '00:00:00'
            }

        elif report_type == 'refueling':
            return {
                'totalVehicles': len(details),
                'totalFuelConsumption': sum(item.get('actualConsumption', 0) for item in details),
                'totalRefills': sum(item.get('refillVolume', 0) for item in details),
                'avgEfficiency': sum(item.get('consumptionPer100km', 0) for item in details) / len(details)
            }

        elif report_type == 'violations':
            return {
                'totalVehicles': len(details),
                'totalViolations': len([item for item in details if item.get('violationType') != 'Нет нарушений']),
                'totalPenaltyPoints': len(
                    [item for item in details if item.get('violationType') != 'Нет нарушений']) * 5
            }

        elif report_type == 'summary':
            return {
                'totalVehicles': len(details),
                'totalDistance': sum(item.get('distance', 0) for item in details),
                'totalFuelConsumption': sum(item.get('fuelConsumption', 0) for item in details),
                'totalViolations': sum(item.get('violationsCount', 0) for item in details),
                'avgSpeed': sum(item.get('avgSpeed', 0) for item in details) / len(details)
            }

        else:
            return {
                'totalVehicles': len(details),
                'totalRecords': len(details)
            }

    def _calculate_average_speed(self, trips_data):
        """Расчет средней скорости"""
        if not trips_data:
            return 0
        speeds = [trip.get('avg_speed', 0) for trip in trips_data if trip.get('avg_speed')]
        return sum(speeds) / len(speeds) if speeds else 0

    def _calculate_max_speed(self, trips_data):
        """Расчет максимальной скорости"""
        if not trips_data:
            return 0
        return max([trip.get('max_speed', 0) for trip in trips_data])

    def _get_last_fuel_level(self, track_data):
        """Получение последнего уровня топлива"""
        if not track_data:
            return 0
        return track_data[-1].get('fuel_level', 0) if track_data else 0

    def _get_last_location(self, track_data):
        """Получение последнего местоположения"""
        if not track_data:
            return 'Не определено'
        last_point = track_data[-1]
        lat = last_point.get('coordinates', {}).get('lat')
        lng = last_point.get('coordinates', {}).get('lng')
        return f"{lat}, {lng}" if lat and lng else 'Не определено'

    def _calculate_idle_time(self, work_analysis):
        """Расчет времени простоя"""
        if not work_analysis:
            return '00:00:00'
        parking_seconds = work_analysis.get('parking_engine_off', {}).get('seconds', 0)
        hours = parking_seconds // 3600
        minutes = (parking_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}:00"


class ReportTypesAPI(APIView):
    """API для получения доступных типов отчетов"""

    def get(self, request):
        report_types = [
            {
                'id': 'movement',
                'name': 'Движение',
                'description': 'Анализ движения транспортных средств',
                'icon': 'road'
            },
            {
                'id': 'journal',
                'name': 'Журнал',
                'description': 'Журнал событий и операций',
                'icon': 'book'
            },
            {
                'id': 'refueling',
                'name': 'Заправки и сливы',
                'description': 'Учет топлива: заправки и расход',
                'icon': 'gas-pump'
            },
            {
                'id': 'violations',
                'name': 'Нарушения',
                'description': 'Нарушения правил эксплуатации',
                'icon': 'exclamation-triangle'
            },
            {
                'id': 'shift',
                'name': 'Посменный отчет',
                'description': 'Работа по сменам',
                'icon': 'users'
            },
            {
                'id': 'group',
                'name': 'Работа группы',
                'description': 'Сравнительный анализ группы ТС',
                'icon': 'layer-group'
            },
            {
                'id': 'summary',
                'name': 'Сводный отчёт',
                'description': 'Общая статистика по всем показателям',
                'icon': 'chart-bar'
            },
            {
                'id': 'events',
                'name': 'События',
                'description': 'Хронология событий',
                'icon': 'calendar-alt'
            },
            {
                'id': 'statistics',
                'name': 'Статистика',
                'description': 'Детальная статистика работы',
                'icon': 'chart-line'
            },
            {
                'id': 'parking',
                'name': 'Стоянки',
                'description': 'Анализ времени и мест стоянок',
                'icon': 'parking'
            }
        ]

        return Response({
            "success": True,
            "data": report_types
        })