# debug_api_parameters.py
import os
import sys
import django
from pathlib import Path

# Настройка Django
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
import json
from datetime import datetime, timedelta


def debug_api_parameters():
    client = Client()

    print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ПАРАМЕТРОВ API")
    print("=" * 70)

    # Тестовые данные
    test_vehicle_id = '11804e75-d2c3-4f2b-9107-5ad899adfe12'
    today = datetime.now().date()
    start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    endpoints_to_test = [
        {
            'name': 'HEALTH CHECK',
            'url': '/vehicles/api/health-check/',
            'params': {},
            'method': 'GET'
        },
        {
            'name': 'ENHANCED SUMMARY',
            'url': '/vehicles/api/enhanced-summary/',
            'params': {},
            'method': 'GET'
        },
        {
            'name': 'WORK ANALYSIS',
            'url': '/vehicles/api/work-analysis/',
            'params': {
                'vehicle_id': test_vehicle_id,
                'start_date': start_date,
                'end_date': end_date
            },
            'method': 'GET'
        },
        {
            'name': 'FUEL ANALYSIS',
            'url': '/vehicles/api/fuel-analysis/',
            'params': {
                'vehicle_id': test_vehicle_id,
                'start_date': start_date,
                'end_date': end_date
            },
            'method': 'GET'
        },
        {
            'name': 'VEHICLE TRIPS DETAILED',
            'url': '/vehicles/api/vehicle-trips-detailed/',
            'params': {
                'vehicle_id': test_vehicle_id,
                'start_date': start_date,
                'end_date': end_date
            },
            'method': 'GET'
        },
        {
            'name': 'ENHANCED ANALYTICS',
            'url': '/vehicles/api/enhanced-analytics/',
            'params': {
                'vehicle_ids': test_vehicle_id,
                'start_date': start_date,
                'end_date': end_date
            },
            'method': 'GET'
        }
    ]

    for endpoint in endpoints_to_test:
        print(f"\n🎯 ТЕСТ: {endpoint['name']}")
        print("-" * 50)

        print(f"📤 ЗАПРОС:")
        print(f"   URL: {endpoint['url']}")
        print(f"   Метод: {endpoint['method']}")
        print(f"   Параметры: {json.dumps(endpoint['params'], indent=2, ensure_ascii=False)}")

        try:
            if endpoint['method'] == 'GET':
                response = client.get(endpoint['url'], endpoint['params'])
            else:
                response = client.post(endpoint['url'], endpoint['params'])

            print(f"📥 ОТВЕТ:")
            print(f"   Статус: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success: {data.get('success', 'N/A')}")

                    if data.get('success'):
                        print(f"   📊 Данные получены:")
                        if 'data' in data:
                            response_data = data['data']
                            if isinstance(response_data, dict):
                                print(f"      Ключи: {list(response_data.keys())}")
                                # Покажем немного данных для примера
                                for key, value in list(response_data.items())[:3]:
                                    if isinstance(value, (list, dict)):
                                        print(
                                            f"      {key}: {type(value).__name__} (длина: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                                    else:
                                        print(f"      {key}: {value}")
                            elif isinstance(response_data, list):
                                print(f"      Данные: список (длина: {len(response_data)})")
                                if response_data:
                                    print(f"      Первый элемент: {type(response_data[0])}")
                            else:
                                print(f"      Тип данных: {type(response_data)}")
                        else:
                            print(f"      📄 Прямой ответ: {data}")
                    else:
                        print(f"   ❌ Ошибка API: {data.get('error', 'Unknown error')}")

                except json.JSONDecodeError:
                    print(f"   ❌ Ответ не в JSON формате")
                    print(f"   📄 Содержимое: {response.content[:500]}...")

            else:
                print(f"   ❌ HTTP ошибка: {response.status_code}")
                print(f"   📄 Ответ: {response.content[:500]}...")

        except Exception as e:
            print(f"   💥 Исключение: {e}")
            import traceback
            print(f"   🔍 Трассировка: {traceback.format_exc()}")


def test_service_directly():
    """Прямое тестирование сервисов с выводом параметров"""
    print("\n\n🔧 ПРЯМОЕ ТЕСТИРОВАНИЕ СЕРВИСОВ С ПАРАМЕТРАМИ")
    print("=" * 70)

    from vehicles.services_enhanced import EnhancedAutoGraphService

    service = EnhancedAutoGraphService()

    # Аутентификация
    print("\n1. 🔐 АУТЕНТИФИКАЦИЯ...")
    if service.login("Osipenko", "Osipenko"):
        print("   ✅ Успешно")
        schemas = service.get_schemas()
        if schemas:
            schema_id = schemas[0].get('ID')
            print(f"   📋 Schema ID: {schema_id}")

            # Тест работы сервисов с параметрами
            test_vehicle_id = '11804e75-d2c3-4f2b-9107-5ad899adfe12'
            start_date = '2025-11-17'
            end_date = '2025-11-18'

            print(f"\n2. 🚗 ТЕСТ С ПАРАМЕТРАМИ:")
            print(f"   Vehicle ID: {test_vehicle_id}")
            print(f"   Start Date: {start_date}")
            print(f"   End Date: {end_date}")

            # Тест work analysis
            print(f"\n3. 🔧 WORK ANALYSIS...")
            try:
                work_result = service.get_work_analysis(schema_id, test_vehicle_id, start_date, end_date)
                print(f"   ✅ Результат: {work_result}")
                if work_result:
                    print(f"      - Движение: {work_result.engine_work_in_motion} сек")
                    print(f"      - Простой с двигателем: {work_result.engine_work_without_movement} сек")
                    print(f"      - Простой без двигателя: {work_result.parking_engine_off} сек")
                    print(f"      - Нет данных: {work_result.no_data} сек")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                import traceback
                print(f"   🔍 Детали: {traceback.format_exc()}")

            # Тест fuel analysis
            print(f"\n4. ⛽ FUEL ANALYSIS...")
            try:
                fuel_result = service.get_fuel_consumption_analysis(schema_id, test_vehicle_id, start_date, end_date)
                print(f"   ✅ Результат: {fuel_result}")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

            # Тест trips detailed
            print(f"\n5. 🛣️ TRIPS DETAILED...")
            try:
                trips_result = service.get_vehicle_trips_detailed(schema_id, test_vehicle_id, start_date, end_date)
                print(f"   ✅ Получено рейсов: {len(trips_result) if trips_result else 0}")
                if trips_result:
                    for i, trip in enumerate(trips_result[:2]):  # Покажем первые 2
                        print(f"      Рейс {i + 1}: {trip.start_time} -> {trip.end_time}, {trip.distance} км")
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")

        else:
            print("   ❌ Нет схем")
    else:
        print("   ❌ Ошибка аутентификации")


def check_vehicle_availability():
    """Проверка доступности vehicle_id"""
    print("\n\n🔎 ПРОВЕРКА ДОСТУПНЫХ VEHICLE_ID")
    print("=" * 70)

    from vehicles.services_enhanced import EnhancedAutoGraphService

    service = EnhancedAutoGraphService()

    if service.login("Osipenko", "Osipenko"):
        schemas = service.get_schemas()
        if schemas:
            schema_id = schemas[0].get('ID')
            vehicles = service.get_vehicles(schema_id)

            if vehicles and 'Items' in vehicles:
                print(f"📋 Доступные Vehicle ID ({len(vehicles['Items'])} шт):")
                for i, vehicle in enumerate(vehicles['Items']):
                    status = "✅" if vehicle.get('ID') == '11804e75-d2c3-4f2b-9107-5ad899adfe12' else "  "
                    print(f"   {status} {i + 1:2d}. ID: {vehicle.get('ID')}")
                    print(f"        Name: {vehicle.get('Name')}")
                    print(f"        Serial: {vehicle.get('Serial')}")
                    if i >= 4:  # Покажем только первые 5
                        print(f"        ... и еще {len(vehicles['Items']) - 5} ТС")
                        break


if __name__ == "__main__":
    print("🚀 ЗАПУСК ДЕТАЛЬНОЙ ДИАГНОСТИКИ API И ПАРАМЕТРОВ")
    print("=" * 70)

    debug_api_parameters()
    test_service_directly()
    check_vehicle_availability()

    print("\n🎯 ДИАГНОСТИКА ЗАВЕРШЕНА")