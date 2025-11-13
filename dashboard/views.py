# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from vehicles.services import AutoGraphService
import logging

logger = logging.getLogger(__name__)


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


@login_required
def dashboard(request):
    """ОСНОВНОЙ дашборд с улучшенными данными (включая топливо)"""
    try:
        service = AutoGraphService()
        # Используем ваши реальные учетные данные вместо demo
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')
                schema_name = schemas[0].get('Name', 'Основная схема')

                # ИСПОЛЬЗУЕМ УЛУЧШЕННЫЙ МЕТОД С ТОПЛИВОМ
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                if dashboard_data:
                    context = {
                        'schema_name': schema_name,
                        'total_vehicles': dashboard_data.get('total_vehicles', 0),
                        'online_vehicles': dashboard_data.get('online_vehicles', 0),
                        'offline_vehicles': dashboard_data.get('offline_vehicles', 0),
                        'moving_vehicles': len([v for v in dashboard_data.get('vehicles', []) if v.get('speed', 0) > 0]),
                        'vehicles': dashboard_data.get('vehicles', []),
                        'current_time': timezone.now(),
                        'last_update': dashboard_data.get('last_update'),
                        # Добавляем счетчик ТС с данными о топливе
                        'vehicles_with_fuel': len([v for v in dashboard_data.get('vehicles', []) if v.get('fuel_level') is not None]),
                    }
                else:
                    # Fallback если данные не получены
                    context = {
                        'schema_name': schema_name,
                        'total_vehicles': 0,
                        'online_vehicles': 0,
                        'offline_vehicles': 0,
                        'moving_vehicles': 0,
                        'vehicles': [],
                        'current_time': timezone.now(),
                        'vehicles_with_fuel': 0,
                    }

                return render(request, 'dashboard/dashboard.html', context)

        # Fallback если сервис недоступен
        context = {
            'schema_name': 'Основная схема',
            'total_vehicles': 0,
            'online_vehicles': 0,
            'offline_vehicles': 0,
            'moving_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
            'vehicles_with_fuel': 0,
        }
        return render(request, 'dashboard/dashboard.html', context)

    except Exception as e:
        logger.error(f"Dashboard view error: {e}")
        context = {
            'schema_name': 'Основная схема',
            'total_vehicles': 0,
            'online_vehicles': 0,
            'offline_vehicles': 0,
            'moving_vehicles': 0,
            'vehicles': [],
            'current_time': timezone.now(),
            'vehicles_with_fuel': 0,
        }
        return render(request, 'dashboard/dashboard.html', context)


@login_required
def debug_online(request):
    """Страница для отладки онлайн данных"""
    try:
        service = AutoGraphService()
        if service.login("demo", "demo"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем сырые данные для отладки
                online_data = service.debug_online_data(schema_id)

                context = {
                    'online_data': online_data,
                    'schema_name': schemas[0].get('Name', 'Demo'),
                    'current_time': timezone.now(),
                }
                return render(request, 'dashboard/debug_online.html', context)

    except Exception as e:
        logger.error(f"Debug error: {e}")

    return render(request, 'dashboard/debug_online.html', {
        'online_data': {},
        'schema_name': 'Demo',
        'current_time': timezone.now(),
    })


@login_required
def vehicles_page(request):
    """Страница транспорта с реальными данными"""
    try:
        service = AutoGraphService()
        if service.login("demo", "demo"):
            schemas = service.get_schemas()
            if schemas:
                first_schema = schemas[0]
                schema_id = first_schema.get('ID')
                schema_name = first_schema.get('Name', 'Demo')

                vehicles_data = service.get_vehicles(schema_id)
                all_vehicles = []

                if vehicles_data and 'Items' in vehicles_data:
                    for item in vehicles_data['Items']:
                        vehicle = {
                            'id': item.get('ID'),
                            'name': item.get('Name', 'Без названия'),
                            'license_plate': extract_license_plate(item),
                            'serial': item.get('Serial'),
                            'allowed': item.get('Allowed', False),
                        }
                        all_vehicles.append(vehicle)

                context = {
                    'all_vehicles': all_vehicles,
                    'schema_name': schema_name,
                    'current_time': timezone.now(),
                }
                return render(request, 'vehicles/vehicles.html', context)

        return render(request, 'vehicles/vehicles.html', {
            'all_vehicles': [],
            'schema_name': 'Demo',
            'current_time': timezone.now(),
        })

    except Exception as e:
        logger.error(f"Ошибка получения данных транспорта: {e}")
        return render(request, 'vehicles/vehicles.html', {
            'all_vehicles': [],
            'schema_name': 'Demo',
            'current_time': timezone.now(),
        })


@login_required
def reports(request):
    return render(request, 'reports/reports.html')


@login_required
def retransmission(request):
    return render(request, 'retransmission/retransmission.html')


@login_required
def billing(request):
    return render(request, 'billing/billing.html')


@login_required
def support(request):
    return render(request, 'support/support.html')


@login_required
def test_all_properties_apis(request):
    """Тестируем все API методы для получения свойств ТС"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем несколько ТС для тестирования
                vehicles_data = service.get_vehicles(schema_id)
                if vehicles_data and 'Items' in vehicles_data:
                    # Берем первые 2 ТС для тестирования
                    test_vehicles = vehicles_data['Items'][:2]
                    vehicle_ids = [str(v.get('ID')) for v in test_vehicles]

                    results = {}

                    # 1. Детальный анализ GetProperties
                    print("\n" + "=" * 50)
                    print("DETAILED PROPERTIES ANALYSIS")
                    print("=" * 50)
                    results['GetProperties_Detailed'] = service.debug_properties_structure(schema_id, vehicle_ids)

                    # 2. GetPropertiesTable (если есть)
                    print("\n" + "=" * 50)
                    print("GET PROPERTIES TABLE")
                    print("=" * 50)
                    results['GetPropertiesTable'] = service.get_vehicle_properties_table(schema_id, vehicle_ids)

                    # 3. EnumDevices свойства
                    print("\n" + "=" * 50)
                    print("ENUM DEVICES PROPERTIES")
                    print("=" * 50)
                    results['EnumDevices'] = {}
                    for vehicle in test_vehicles:
                        vehicle_id = str(vehicle.get('ID'))
                        results['EnumDevices'][vehicle_id] = {
                            'name': vehicle.get('Name'),
                            'properties_from_enum': vehicle.get('properties', [])
                        }
                        print(f"Vehicle {vehicle_id} - {vehicle.get('Name')}")
                        print(f"Properties from EnumDevices: {vehicle.get('properties', [])}")

                    context = {
                        'test_vehicles': test_vehicles,
                        'results': results,
                        'schema_name': schemas[0].get('Name', 'Основная схема'),
                    }
                    return render(request, 'dashboard/test_apis.html', context)

    except Exception as e:
        logger.error(f"Test APIs error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_apis.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_enhanced_dashboard(request):
    """Тестируем улучшенный метод дашборда"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Тестируем улучшенный метод
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                context = {
                    'dashboard_data': dashboard_data,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                }
                return render(request, 'dashboard/test_enhanced.html', context)

    except Exception as e:
        logger.error(f"Test enhanced dashboard error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_enhanced.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_online_apis(request):
    """Тестируем все API методы для онлайн данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем несколько ТС для тестирования
                vehicles_data = service.get_vehicles(schema_id)
                if vehicles_data and 'Items' in vehicles_data:
                    # Берем первые 2 ТС для тестирования
                    test_vehicles = vehicles_data['Items'][:2]
                    vehicle_ids = [str(v.get('ID')) for v in test_vehicles]

                    results = {}

                    # 1. GetOnlineInfoAll - который мы уже используем
                    print("\n" + "=" * 50)
                    print("GETONLINEINFOALL")
                    print("=" * 50)
                    results['GetOnlineInfoAll'] = service.get_online_info_all(schema_id)

                    # 2. GetOnlineInfo - для конкретных устройств
                    print("\n" + "=" * 50)
                    print("GETONLINEINFO")
                    print("=" * 50)
                    results['GetOnlineInfo'] = service.get_online_info(schema_id, vehicle_ids)

                    # 3. GetDevicesInfo - может содержать онлайн данные
                    print("\n" + "=" * 50)
                    print("GETDEVICESINFO")
                    print("=" * 50)
                    results['GetDevicesInfo'] = service.get_devices_info(schema_id, vehicle_ids)

                    # 4. GetOnlineInfo с другими параметрами
                    print("\n" + "=" * 50)
                    print("GETONLINEINFO WITH FINAL PARAMS")
                    print("=" * 50)
                    results['GetOnlineInfo_Extended'] = service.get_online_info_extended(schema_id, vehicle_ids)

                    context = {
                        'test_vehicles': test_vehicles,
                        'results': results,
                        'schema_name': schemas[0].get('Name', 'Основная схема'),
                    }
                    return render(request, 'dashboard/test_online_apis.html', context)

    except Exception as e:
        logger.error(f"Test online APIs error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_online_apis.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_parsing(request):
    """Тестируем парсинг онлайн данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем онлайн данные
                online_info = service.get_online_info_all(schema_id)

                # Тестируем парсинг для первых 2 ТС
                test_results = {}
                for vehicle_id in list(online_info.keys())[:2]:
                    parsed_data = service.parse_online_data(online_info, vehicle_id)
                    test_results[vehicle_id] = {
                        'raw_data': online_info.get(vehicle_id, {}),
                        'parsed_data': parsed_data
                    }

                context = {
                    'test_results': test_results,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                }
                return render(request, 'dashboard/test_parsing.html', context)

    except Exception as e:
        logger.error(f"Test parsing error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_parsing.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_final_dashboard(request):
    """Финальный тест дашборда"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Используем улучшенный метод
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                context = {
                    'dashboard_data': dashboard_data,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                }
                return render(request, 'dashboard/test_final.html', context)

    except Exception as e:
        logger.error(f"Test final dashboard error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_final.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_fuel_sources(request):
    """Тестируем источники данных по топливу"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем несколько ТС для тестирования
                vehicles_data = service.get_vehicles(schema_id)
                if vehicles_data and 'Items' in vehicles_data:
                    # Берем первые 3 ТС
                    test_vehicles = vehicles_data['Items'][:3]
                    vehicle_ids = [str(v.get('ID')) for v in test_vehicles]

                    results = {}

                    # 1. GetOnlineInfoAll - текущий источник
                    results['GetOnlineInfoAll'] = service.get_online_info_all(schema_id)

                    # 2. GetOnlineInfo - расширенная информация
                    results['GetOnlineInfo'] = service.get_online_info(schema_id, vehicle_ids)

                    # 3. GetPropertiesTable - свойства с датчиками
                    results['GetPropertiesTable'] = service.get_vehicle_properties_table(schema_id, vehicle_ids)

                    # 4. Проверим GetOnlineInfo с параметрами топлива
                    results['GetOnlineInfo_Fuel'] = service.get_online_info_with_fuel(schema_id, vehicle_ids)

                    context = {
                        'test_vehicles': test_vehicles,
                        'results': results,
                        'schema_name': schemas[0].get('Name', 'Основная схема'),
                    }
                    return render(request, 'dashboard/test_fuel.html', context)

    except Exception as e:
        logger.error(f"Test fuel sources error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_fuel.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_final_fuel(request):
    """Финальный тест с исправленным источником данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Используем улучшенный метод
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                context = {
                    'dashboard_data': dashboard_data,
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                }
                return render(request, 'dashboard/test_final_fuel.html', context)

    except Exception as e:
        logger.error(f"Test final fuel error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_final_fuel.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def debug_fuel_parsing(request):
    """Отладка парсинга топлива"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем несколько ТС
                vehicles_data = service.get_vehicles(schema_id)
                if vehicles_data and 'Items' in vehicles_data:
                    # Берем первые 2 ТС
                    test_vehicles = vehicles_data['Items'][:2]
                    vehicle_ids = [str(v.get('ID')) for v in test_vehicles]

                    # Получаем данные с топливом
                    online_info = service.get_online_info_with_fuel(schema_id, vehicle_ids)

                    # Тестируем парсинг
                    parsing_results = {}
                    for vehicle_id in vehicle_ids:
                        if vehicle_id in online_info:
                            raw_data = online_info[vehicle_id]
                            parsed_data = service.parse_online_data(online_info, vehicle_id)
                            parsing_results[vehicle_id] = {
                                'raw_final': raw_data.get('Final', {}),
                                'parsed_fuel': parsed_data.get('fuel_level') if parsed_data else None
                            }

                    context = {
                        'test_vehicles': test_vehicles,
                        'parsing_results': parsing_results,
                        'online_info_sample': online_info,
                    }
                    return render(request, 'dashboard/debug_fuel_parsing.html', context)

    except Exception as e:
        logger.error(f"Debug fuel parsing error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/debug_fuel_parsing.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def test_final_with_fuel(request):
    """Финальный тест с исправленным источником данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Используем улучшенный метод
                dashboard_data = service.get_enhanced_dashboard_summary(schema_id)

                # Посчитаем ТС с топливом
                vehicles_with_fuel = [v for v in dashboard_data.get('vehicles', []) if v.get('fuel_level') is not None]

                context = {
                    'dashboard_data': dashboard_data,
                    'vehicles_with_fuel': len(vehicles_with_fuel),
                    'schema_name': schemas[0].get('Name', 'Основная схема'),
                }
                return render(request, 'dashboard/test_final_with_fuel.html', context)

    except Exception as e:
        logger.error(f"Test final with fuel error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/test_final_with_fuel.html', {
        'error': 'Не удалось получить данные'
    })


@login_required
def debug_raw_data(request):
    """Отладка сырых данных"""
    try:
        service = AutoGraphService()
        if service.login("Osipenko", "Osipenko"):
            schemas = service.get_schemas()
            if schemas:
                schema_id = schemas[0].get('ID')

                # Получаем все ТС
                vehicles_data = service.get_vehicles(schema_id)
                device_ids = [str(v.get('ID')) for v in vehicles_data.get('Items', [])]

                # Получаем разные источники данных
                online_info_all = service.get_online_info_all(schema_id)
                online_info_fuel = service.get_online_info_with_fuel(schema_id, device_ids[:5])  # первые 5 для теста

                context = {
                    'online_info_all_sample': dict(list(online_info_all.items())[:2]) if online_info_all else {},
                    'online_info_fuel_sample': online_info_fuel,
                    'device_ids': device_ids[:5],
                }
                return render(request, 'dashboard/debug_raw_data.html', context)

    except Exception as e:
        logger.error(f"Debug raw data error: {e}")
        import traceback
        logger.error(traceback.format_exc())

    return render(request, 'dashboard/debug_raw_data.html', {
        'error': 'Не удалось получить данные'
    })