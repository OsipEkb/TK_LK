import requests
import json
from datetime import datetime, timedelta


def test_autograph_api():
    """Тестовый скрипт для проверки AutoGRAPH API"""

    # Данные для подключения
    BASE_URL = "https://web.tk-ekat.ru/"  # замени на реальный URL
    USERNAME = "Osipenko"  # тестовый логин
    PASSWORD = "Osipenko"  # тестовый пароль

    session = requests.Session()

    try:
        # 1. Аутентификация
        print("🔐 1. Аутентификация...")
        login_url = f"{BASE_URL}/ServiceJSON/Login"
        params = {
            'UserName': USERNAME,
            'Password': PASSWORD,
            'UTCOffset': 180  # Moscow UTC+3
        }

        response = session.get(login_url, params=params)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")

        if response.status_code != 200 or not response.text.strip():
            print("❌ Ошибка аутентификации")
            return

        token = response.text.strip('"')
        print(f"✅ Токен получен: {token[:20]}...")

        # 2. Получение списка схем
        print("\n📋 2. Получение схем...")
        schemas_url = f"{BASE_URL}/ServiceJSON/EnumSchemas"
        params = {'session': token}

        response = session.get(schemas_url, params=params)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            schemas = response.json()
            print(f"✅ Получено схем: {len(schemas)}")
            for schema in schemas[:2]:  # покажем первые 2
                print(f"   - {schema.get('Name')} (ID: {schema.get('ID')})")
        else:
            print("❌ Ошибка получения схем")
            return

        if not schemas:
            print("❌ Нет доступных схем")
            return

        schema_id = schemas[0]['ID']

        # 3. Получение списка ТС
        print(f"\n🚗 3. Получение ТС для схемы {schema_id}...")
        vehicles_url = f"{BASE_URL}/ServiceJSON/EnumDevices"
        params = {
            'session': token,
            'schemaID': schema_id
        }

        response = session.get(vehicles_url, params=params)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            vehicles_data = response.json()
            items = vehicles_data.get('Items', [])
            print(f"✅ Получено ТС: {len(items)}")
            for vehicle in items[:3]:  # покажем первые 3
                print(f"   - {vehicle.get('Name')} (ID: {vehicle.get('ID')})")
        else:
            print("❌ Ошибка получения ТС")
            return

        # 4. Тестирование метода для графиков
        print(f"\n📊 4. Тестирование данных для графиков...")

        # Получаем параметры ТС
        if items:
            vehicle_id = items[0]['ID']
            print(f"   Тестируем ТС: {vehicle_id}")

            # Метод GetTripTables для графиков
            trips_url = f"{BASE_URL}/ServiceJSON/GetTripTables"

            # Форматируем даты
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)

            params = {
                'session': token,
                'schemaID': schema_id,
                'IDs': vehicle_id,
                'SD': start_date.strftime('%Y%m%d'),
                'ED': end_date.strftime('%Y%m%d'),
                'onlineParams': 'FuelLevel,Speed,EngineHours',  # базовые параметры
                'tripSplitterIndex': -1
            }

            response = session.get(trips_url, params=params)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                chart_data = response.json()
                print(f"✅ Получены данные для графиков")
                print(f"   Структура ответа: {list(chart_data.keys()) if chart_data else 'пусто'}")

                # Сохраним пример ответа в файл для анализа
                with open('autograph_response_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(chart_data, f, ensure_ascii=False, indent=2)
                print("💾 Пример ответа сохранен в autograph_response_sample.json")

            else:
                print(f"❌ Ошибка получения данных графиков: {response.text}")

        print("\n✅ Тестирование завершено!")

    except Exception as e:
        print(f"💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_autograph_api()