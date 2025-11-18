# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000/vehicles"


def test_debug_api():
    """Тест полной диагностики API"""
    print("🧪 ТЕСТ ПОЛНОЙ ДИАГНОСТИКИ API")
    print("=" * 50)

    params = {
        'vehicle_id': '11804e75-d2c3-4f2b-9107-5ad899adfe12',
        'start_date': '20251117-0000',
        'end_date': '20251117-2359'
    }

    response = requests.get(f"{BASE_URL}/api/debug/", params=params)

    if response.status_code == 200:
        data = response.json()
        print("✅ Диагностика завершена")
        print(f"📋 Результат: {data}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)


def test_work_analysis():
    """Тест анализа работы"""
    print("\n🧪 ТЕСТ АНАЛИЗА РАБОТЫ")
    print("=" * 50)

    params = {
        'vehicle_id': '11804e75-d2c3-4f2b-9107-5ad899adfe12',
        'start_date': '20251117-0800',
        'end_date': '20251117-1800'
    }

    response = requests.get(f"{BASE_URL}/api/work-analysis/", params=params)

    if response.status_code == 200:
        data = response.json()
        print("✅ Work Analysis успешно")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)


def test_all_endpoints():
    """Тест всех эндпоинтов"""
    print("\n🧪 ТЕСТ ВСЕХ ЭНДПОИНТОВ")
    print("=" * 50)

    vehicle_id = '11804e75-d2c3-4f2b-9107-5ad899adfe12'

    endpoints = [
        ('/api/debug/', {'vehicle_id': vehicle_id}),
        ('/api/work-analysis/', {'vehicle_id': vehicle_id}),
        ('/api/summary/', {}),
        ('/api/health/', {}),
    ]

    for endpoint, params in endpoints:
        print(f"\n🔗 Тестируем {endpoint}")
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Успех: {data.get('success', False)}")
            if 'data' in data:
                print(f"📊 Данные получены")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")


if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТОВ AUTOGRAPH API")
    print("=" * 50)

    test_debug_api()
    test_work_analysis()
    test_all_endpoints()

    print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")