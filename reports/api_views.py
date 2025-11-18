from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from vehicles.services import AutoGraphService, AutoGraphHistoricalService
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ReportsVehicleListAPI(APIView):
    """API для получения списка ТС для страницы отчетов"""

    def get(self, request):
        try:
            service = AutoGraphService()

            if not service.login("Osipenko", "Osipenko"):
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
                license_plate = service.extract_license_plate_enhanced(vehicle)

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
            start_time = data.get('start_time', '00:00')
            end_time = data.get('end_time', '23:59')

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
                report_type, vehicle_ids, start_date, end_date, start_time, end_time
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

    def _generate_report(self, report_type, vehicle_ids, start_date, end_date, start_time, end_time):
        """Генерация данных отчета"""

        # Используем сервис для получения данных
        service = AutoGraphService()
        historical_service = AutoGraphHistoricalService()

        if not service.login("Osipenko", "Osipenko"):
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
                # Получаем исторические данные для ТС
                historical_data = historical_service.get_vehicle_historical_statistics(
                    username="Osipenko",
                    password="Osipenko",
                    vehicle_id=vehicle_id,
                    schema_id=schema_id,
                    start_date=start_date,
                    end_date=end_date
                )

                if historical_data and historical_data.get('transformation_success'):
                    vehicle_report = self._format_vehicle_report(
                        report_type, historical_data, vehicle_id
                    )
                    report_data["details"].append(vehicle_report)
                    report_data["vehicles"].append({
                        'id': vehicle_id,
                        'name': historical_data.get('vehicle_name', 'Unknown'),
                        'license_plate': historical_data.get('license_plate', 'Unknown')
                    })

            except Exception as e:
                logger.error(f"Error processing vehicle {vehicle_id}: {e}")
                continue

        # Рассчитываем сводную статистику
        report_data["summary"] = self._calculate_summary_stats(report_data["details"], report_type)

        return report_data

    def _format_vehicle_report(self, report_type, historical_data, vehicle_id):
        """Форматирование данных отчета для конкретного ТС"""

        summary = historical_data.get('summary', {})
        fuel_analytics = historical_data.get('fuel_analytics', {})
        violations = historical_data.get('violations', {})

        base_data = {
            'vehicle_id': vehicle_id,
            'vehicle_name': historical_data.get('vehicle_name', 'Unknown'),
            'license_plate': historical_data.get('license_plate', 'Unknown'),
        }

        if report_type == 'movement':
            return {
                **base_data,
                'distance': summary.get('total_distance', 0),
                'avg_speed': summary.get('average_speed', 0),
                'max_speed': summary.get('max_speed', 0),
                'move_duration': summary.get('total_move_duration', '00:00:00'),
                'engine_hours': summary.get('total_engine_hours', '00:00:00'),
                'parking_count': summary.get('parking_count', 0)
            }
        elif report_type == 'refueling':
            return {
                **base_data,
                'fuel_consumption': summary.get('total_fuel_consumption', 0),
                'fuel_efficiency': summary.get('fuel_efficiency', 0),
                'refills_count': fuel_analytics.get('refills_count', 0),
                'refills_volume': fuel_analytics.get('refills_volume', 0),
                'current_level': fuel_analytics.get('current_level', 0)
            }
        elif report_type == 'violations':
            return {
                **base_data,
                'overspeed_count': summary.get('overspeed_count', 0),
                'overspeed_duration': violations.get('overspeed_duration', '00:00:00'),
                'penalty_points': violations.get('penalty_points', 0),
                'overspeed_points': violations.get('overspeed_points', 0)
            }
        elif report_type == 'summary':
            return {
                **base_data,
                'distance': summary.get('total_distance', 0),
                'fuel_consumption': summary.get('total_fuel_consumption', 0),
                'engine_hours': summary.get('total_engine_hours', '00:00:00'),
                'avg_speed': summary.get('average_speed', 0),
                'violations_count': summary.get('overspeed_count', 0),
                'parking_count': summary.get('parking_count', 0)
            }
        else:
            return base_data

    def _calculate_summary_stats(self, details, report_type):
        """Расчет сводной статистики"""
        if not details:
            return {}

        if report_type == 'movement':
            total_distance = sum(item.get('distance', 0) for item in details)
            total_vehicles = len(details)
            avg_speed = sum(item.get('avg_speed', 0) for item in details) / total_vehicles if total_vehicles > 0 else 0

            return {
                'total_vehicles': total_vehicles,
                'total_distance': round(total_distance, 2),
                'average_speed': round(avg_speed, 2),
                'total_parking_count': sum(item.get('parking_count', 0) for item in details)
            }

        elif report_type == 'refueling':
            total_fuel = sum(item.get('fuel_consumption', 0) for item in details)
            total_refills = sum(item.get('refills_count', 0) for item in details)

            return {
                'total_vehicles': len(details),
                'total_fuel_consumption': round(total_fuel, 2),
                'total_refills': total_refills,
                'average_efficiency': round(sum(item.get('fuel_efficiency', 0) for item in details) / len(details),
                                            2) if details else 0
            }

        elif report_type == 'violations':
            total_violations = sum(item.get('overspeed_count', 0) for item in details)
            total_points = sum(item.get('penalty_points', 0) for item in details)

            return {
                'total_vehicles': len(details),
                'total_violations': total_violations,
                'total_penalty_points': round(total_points, 2),
                'average_violations_per_vehicle': round(total_violations / len(details), 2) if details else 0
            }

        else:  # summary report
            total_distance = sum(item.get('distance', 0) for item in details)
            total_fuel = sum(item.get('fuel_consumption', 0) for item in details)
            total_violations = sum(item.get('violations_count', 0) for item in details)

            return {
                'total_vehicles': len(details),
                'total_distance': round(total_distance, 2),
                'total_fuel_consumption': round(total_fuel, 2),
                'total_violations': total_violations,
                'average_speed': round(sum(item.get('avg_speed', 0) for item in details) / len(details),
                                       2) if details else 0
            }