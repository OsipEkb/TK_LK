# vehicles/api_views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .services import AutoGraphService, AutoGraphHistoricalService, AutoGraphDataCollector
import logging

logger = logging.getLogger(__name__)


class VehicleListAPI(APIView):
    """API для получения списка ТС из AutoGRAPH"""

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            schema_id = request.data.get('schema_id')

            if not all([username, password, schema_id]):
                return Response(
                    {"error": "Необходимы параметры: username, password, schema_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = AutoGraphService()

            if not service.login(username, password):
                return Response(
                    {"error": "Ошибка аутентификации в AutoGRAPH"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            vehicles_data = service.get_vehicles(schema_id)

            return Response(vehicles_data)

        except Exception as e:
            logger.error(f"❌ Error in VehicleListAPI: {e}")
            return Response(
                {"error": f"Ошибка при получении списка ТС: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleListForPageAPI(APIView):
    """API для получения списка ТС для страницы транспорта"""

    def get(self, request):
        try:
            # Используем хардкодированные учетные данные (как в дашборде)
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
            logger.error(f"VehicleListForPageAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VehicleSyncAPI(APIView):
    """API для получения данных из AutoGRAPH (без сохранения в БД)"""

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                return Response(
                    {"error": "Необходимы username и password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = AutoGraphService()

            if not service.login(username, password):
                return Response(
                    {"error": "Ошибка аутентификации в AutoGRAPH"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            schemas = service.get_schemas()
            if not schemas:
                return Response(
                    {"error": "Не удалось получить схемы из AutoGRAPH"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Возвращаем схемы без сохранения в БД
            return Response({
                "message": "Данные успешно получены из AutoGRAPH",
                "schemas_count": len(schemas),
                "schemas": schemas
            })

        except Exception as e:
            logger.error(f"❌ Error in VehicleSyncAPI: {e}")
            return Response(
                {"error": f"Ошибка при синхронизации: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleHistoricalDataAPI(APIView):
    """API для получения исторических данных ТС - ФОРМАТ yyyyMMdd-HHmm"""

    def post(self, request, vehicle_id):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            schema_id = request.data.get('schema_id')

            if not all([username, password, start_date, end_date, schema_id]):
                return Response(
                    {"error": "Необходимы параметры: username, password, start_date, end_date, schema_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            historical_service = AutoGraphHistoricalService()
            historical_data = historical_service.get_vehicle_historical_statistics(
                username=username,
                password=password,
                vehicle_id=vehicle_id,
                schema_id=schema_id,
                start_date=start_date,
                end_date=end_date
            )

            return Response(historical_data)

        except Exception as e:
            logger.error(f"❌ Error in VehicleHistoricalDataAPI: {e}")
            return Response(
                {"error": f"Ошибка при получении исторических данных: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VehicleOnlineDataAPI(APIView):
    """API для получения онлайн-данных ТС"""

    def post(self, request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            schema_id = request.data.get('schema_id')
            vehicle_ids = request.data.get('vehicle_ids')

            if not all([username, password, schema_id]):
                return Response(
                    {"error": "Необходимы параметры: username, password, schema_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            service = AutoGraphService()

            if not service.login(username, password):
                return Response(
                    {"error": "Ошибка аутентификации в AutoGRAPH"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if vehicle_ids:
                online_data = service.get_online_info(schema_id, vehicle_ids)
            else:
                online_data = service.get_online_info_all(schema_id)

            return Response(online_data)

        except Exception as e:
            logger.error(f"❌ Error in VehicleOnlineDataAPI: {e}")
            return Response(
                {"error": f"Ошибка при получении онлайн-данных: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(login_required, name='dispatch')
class VehicleStatisticsAPI(View):
    """УЛУЧШЕННЫЙ API для получения статистики ТС - ФОРМАТ yyyyMMdd-HHmm"""

    def get(self, request):
        try:
            vehicle_id = request.GET.get('vehicle_id')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if not all([vehicle_id, start_date, end_date]):
                return JsonResponse({
                    "success": False,
                    "error": "Необходимы параметры: vehicle_id, start_date, end_date"
                })

            # Используем улучшенный сервис
            historical_service = AutoGraphHistoricalService()
            statistics = historical_service.get_vehicle_historical_statistics(
                username="Osipenko",
                password="Osipenko",
                vehicle_id=vehicle_id,
                schema_id="fad66447-fe18-4a2a-a7b9-945eab775fda",  # ID схемы Osipenko
                start_date=start_date,
                end_date=end_date
            )

            if statistics and statistics.get('transformation_success'):
                return JsonResponse({
                    "success": True,
                    "data": statistics,
                    "message": "Данные успешно получены"
                })
            else:
                # Даже если transformation_success=False, возвращаем данные для отладки
                return JsonResponse({
                    "success": True,  # Все равно возвращаем success=True чтобы показать данные
                    "data": statistics or {},
                    "message": "Данные получены с ограничениями",
                    "debug_info": {
                        "has_data": bool(statistics),
                        "data_source": statistics.get('data_source') if statistics else 'none',
                        "trips_count": statistics.get('trips_count', 0) if statistics else 0
                    }
                })

        except Exception as e:
            logger.error(f"VehicleStatisticsAPI error: {e}")
            return JsonResponse({
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}"
            })


class VehicleDebugAPI(APIView):
    """API для отладки - проверяет подключение к AutoGRAPH"""

    def get(self, request):
        try:
            service = AutoGraphService()

            # 1. Проверяем аутентификацию
            auth_success = service.login("Osipenko", "Osipenko")

            debug_info = {
                "authentication": {
                    "success": auth_success,
                    "token_available": bool(service.token),
                    "token_preview": service.token[:20] + "..." if service.token else None
                }
            }

            if auth_success:
                # 2. Получаем схемы
                schemas = service.get_schemas()
                debug_info["schemas"] = {
                    "count": len(schemas) if isinstance(schemas, list) else 0,
                    "data": schemas
                }

                if schemas and len(schemas) > 0:
                    schema_id = schemas[0].get('ID')

                    # 3. Получаем транспортные средства
                    vehicles_data = service.get_vehicles(schema_id)
                    debug_info["vehicles"] = {
                        "schema_id": schema_id,
                        "has_data": bool(vehicles_data),
                        "items_count": len(vehicles_data.get('Items', [])) if vehicles_data else 0,
                        "sample_items": vehicles_data.get('Items', [])[:3] if vehicles_data else []
                    }

                    # 4. Получаем онлайн данные
                    online_data = service.get_online_info_all(schema_id)
                    debug_info["online_data"] = {
                        "has_data": bool(online_data),
                        "devices_count": len(online_data) if online_data else 0,
                        "sample_devices": list(online_data.keys())[:3] if online_data else []
                    }

            return Response({
                "success": True,
                "debug_info": debug_info
            })

        except Exception as e:
            logger.error(f"VehicleDebugAPI error: {e}")
            import traceback
            return Response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })


class DataCollectionAPI(APIView):
    """API для сбора всех данных из AutoGRAPH - ФОРМАТ yyyyMMdd-HHmm"""

    def post(self, request):
        try:
            username = request.data.get('username', 'Osipenko')
            password = request.data.get('password', 'Osipenko')
            schema_id = request.data.get('schema_id')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')

            collector = AutoGraphDataCollector()
            collected_data = collector.collect_all_data(
                username=username,
                password=password,
                schema_id=schema_id,
                start_date=start_date,
                end_date=end_date
            )

            if collected_data:
                # Сохраняем данные в файл
                filename = collector.save_collected_data()

                return Response({
                    "success": True,
                    "message": f"Данные успешно собраны и сохранены в {filename}",
                    "data_summary": {
                        "schemas_count": len(collected_data.get('schemas', [])),
                        "vehicles_count": len(collected_data.get('vehicles', {}).get('Items', [])),
                        "online_devices_count": len(collected_data.get('online_info_all', {})),
                        "collected_keys": list(collected_data.keys())
                    }
                })
            else:
                return Response({
                    "success": False,
                    "error": "Не удалось собрать данные"
                })

        except Exception as e:
            logger.error(f"DataCollectionAPI error: {e}")
            return Response({
                "success": False,
                "error": f"Ошибка при сборе данных: {str(e)}"
            })


class VehicleHistoricalDebugAPI(APIView):
    """API для диагностики исторических данных - ФОРМАТ yyyyMMdd-HHmm"""

    def get(self, request):
        try:
            vehicle_id = request.GET.get('vehicle_id')
            start_date = request.GET.get('start_date', '2025-11-17')  # Используем дату с данными
            end_date = request.GET.get('end_date', '2025-11-18')

            if not vehicle_id:
                return Response({
                    "success": False,
                    "error": "Необходим параметр vehicle_id"
                })

            service = AutoGraphService()

            # Аутентификация
            if not service.login("Osipenko", "Osipenko"):
                return Response({
                    "success": False,
                    "error": "Ошибка аутентификации"
                })

            # Получаем схемы
            schemas = service.get_schemas()
            if not schemas:
                return Response({
                    "success": False,
                    "error": "Нет доступных схем"
                })

            schema_id = schemas[0].get('ID')

            debug_info = {
                "test_parameters": {
                    "vehicle_id": vehicle_id,
                    "schema_id": schema_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "schema_name": schemas[0].get('Name')
                }
            }

            # 1. Получаем детальную информацию о ТС
            vehicle_details = service.get_vehicle_detailed_info(schema_id, vehicle_id)
            debug_info["vehicle_details"] = vehicle_details

            # 2. Тестируем подключение для исторических данных
            historical_test = service.test_historical_data_connection(
                schema_id, vehicle_id, start_date, end_date
            )
            debug_info["historical_test"] = historical_test

            # 3. Пробуем получить реальные исторические данные
            historical_service = AutoGraphHistoricalService()
            historical_data = historical_service.get_vehicle_historical_statistics(
                username="Osipenko",
                password="Osipenko",
                vehicle_id=vehicle_id,
                schema_id=schema_id,
                start_date=start_date,
                end_date=end_date
            )

            debug_info["historical_data_attempt"] = {
                "success": bool(historical_data),
                "data_source": historical_data.get('data_source') if historical_data else None,
                "transformation_success": historical_data.get('transformation_success') if historical_data else False,
                "trips_count": historical_data.get('trips_count') if historical_data else 0,
                "note": historical_data.get('note') if historical_data else None
            }

            return Response({
                "success": True,
                "debug_info": debug_info
            })

        except Exception as e:
            logger.error(f"VehicleHistoricalDebugAPI error: {e}")
            import traceback
            return Response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })


class TestTripsTotalAPI(APIView):
    """API для тестирования прямого запроса к GetTripsTotal с правильным форматом дат"""

    def get(self, request):
        try:
            vehicle_id = request.GET.get('vehicle_id', '11804e75-d2c3-4f2b-9107-5ad899adfe12')
            start_date = request.GET.get('start_date', '2025-11-17')
            end_date = request.GET.get('end_date', '2025-11-18')

            service = AutoGraphService()

            if not service.login("Osipenko", "Osipenko"):
                return Response({
                    "success": False,
                    "error": "Authentication failed"
                })

            # Форматируем даты правильно - yyyyMMdd-HHmm
            start_fmt = service.format_date_for_api(start_date, is_start=True)
            end_fmt = service.format_date_for_api(end_date, is_start=False)

            logger.info(f"🔍 Testing GetTripsTotal with:")
            logger.info(f"  Vehicle: {vehicle_id}")
            logger.info(f"  Start: {start_fmt}")
            logger.info(f"  End: {end_fmt}")

            # Прямой вызов GetTripsTotal
            trips_data = service.get_trips_total(
                "fad66447-fe18-4a2a-a7b9-945eab775fda",  # schema_id
                vehicle_id,
                start_fmt,
                end_fmt,
                trip_splitter_index=-1
            )

            if trips_data and vehicle_id in trips_data:
                vehicle_data = trips_data[vehicle_id]
                return Response({
                    "success": True,
                    "test_parameters": {
                        "vehicle_id": vehicle_id,
                        "start_date": start_fmt,
                        "end_date": end_fmt,
                        "schema_id": "fad66447-fe18-4a2a-a7b9-945eab775fda"
                    },
                    "data_received": True,
                    "vehicle_name": vehicle_data.get('Name'),
                    "trips_count": len(vehicle_data.get('Trips', [])),
                    "has_total_data": bool(vehicle_data.get('Total')),
                    "sample_data": {
                        "total_distance": vehicle_data.get('Total', {}).get('TotalDistance'),
                        "total_fuel": vehicle_data.get('Total', {}).get('Engine1FuelConsum'),
                        "engine_hours": vehicle_data.get('Total', {}).get('Engine1Motohours')
                    }
                })
            else:
                return Response({
                    "success": False,
                    "error": "No data received",
                    "available_vehicles": list(trips_data.keys()) if trips_data else []
                })

        except Exception as e:
            logger.error(f"❌ TestTripsTotalAPI error: {e}")
            import traceback
            return Response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })