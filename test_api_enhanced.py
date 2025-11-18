# test_api_enhanced.py
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/vehicles"


class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_vehicle_id = '11804e75-d2c3-4f2b-9107-5ad899adfe12'
        self.today = datetime.now().date()
        self.start_date = (self.today - timedelta(days=7)).strftime('%Y-%m-%d')
        self.end_date = self.today.strftime('%Y-%m-%d')

    def print_header(self, title):
        print(f"\n{'=' * 60}")
        print(f"🧪 {title}")
        print(f"{'=' * 60}")

    def print_success(self, message):
        print(f"✅ {message}")

    def print_error(self, message):
        print(f"❌ {message}")

    def print_info(self, message):
        print(f"ℹ️  {message}")

    def test_endpoint(self, endpoint, params=None, method='GET'):
        """Универсальный метод тестирования эндпоинта"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=30)
            else:
                response = requests.post(url, json=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return True, data, response.status_code
            else:
                return False, response.text, response.status_code

        except requests.exceptions.RequestException as e:
            return False, str(e), 0

    def test_health_check(self):
        """Тест проверки здоровья системы"""
        self.print_header("ТЕСТ ПРОВЕРКИ ЗДОРОВЬЯ СИСТЕМЫ")

        success, data, status_code = self.test_endpoint('/api/health-check/')

        if success:
            self.print_success("Health check completed")
            print(f"📊 Status: {data.get('health', {}).get('status', 'unknown')}")
            print(f"🔐 Authentication: {data.get('health', {}).get('authentication', 'unknown')}")
            print(f"📈 Schemas count: {data.get('health', {}).get('schemas_count', 0)}")
        else:
            self.print_error(f"Health check failed: {status_code}")
            print(f"Error: {data}")

    def test_enhanced_summary(self):
        """Тест расширенной сводки"""
        self.print_header("ТЕСТ РАСШИРЕННОЙ СВОДКИ")

        success, data, status_code = self.test_endpoint('/api/enhanced-summary/')

        if success:
            if data.get('success'):
                summary_data = data.get('data', {})
                self.print_success("Enhanced summary completed")
                print(f"🚗 Total vehicles: {summary_data.get('total_vehicles', 0)}")

                status_groups = summary_data.get('status_groups', {})
                for status_type, vehicles in status_groups.items():
                    print(f"  {status_type}: {len(vehicles)} vehicles")

                stats = summary_data.get('summary_stats', {})
                print(f"📊 Total distance: {stats.get('total_distance', 0)} km")
                print(f"⛽ Total fuel: {stats.get('total_fuel', 0)} L")
            else:
                self.print_error(f"API returned error: {data.get('error')}")
        else:
            self.print_error(f"Request failed: {status_code}")
            print(f"Error: {data}")

    def test_work_analysis(self):
        """Тест анализа работы"""
        self.print_header("ТЕСТ АНАЛИЗА РАБОТЫ")

        params = {
            'vehicle_id': self.test_vehicle_id,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        success, data, status_code = self.test_endpoint('/api/work-analysis/', params)

        if success:
            if data.get('success'):
                work_data = data.get('data', {}).get('work_analysis', {})
                self.print_success("Work analysis completed")

                for key, value in work_data.items():
                    if key != 'total_period':
                        print(f"  {key}: {value.get('formatted', 'N/A')} ({value.get('percentage', 0)}%)")
            else:
                self.print_error(f"API returned error: {data.get('error')}")
        else:
            self.print_error(f"Request failed: {status_code}")
            print(f"Error: {data}")

    def test_fuel_analysis(self):
        """Тест анализа топлива"""
        self.print_header("ТЕСТ АНАЛИЗА ТОПЛИВА")

        params = {
            'vehicle_id': self.test_vehicle_id,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        success, data, status_code = self.test_endpoint('/api/fuel-analysis/', params)

        if success:
            if data.get('success'):
                fuel_data = data.get('data', {})
                self.print_success("Fuel analysis completed")

                print(f"⛽ Total fuel: {fuel_data.get('total_fuel_consumption', 0)} L")
                print(f"📏 Total distance: {fuel_data.get('total_distance', 0)} km")
                print(f"📊 Efficiency: {fuel_data.get('fuel_efficiency_100km', 0)} L/100km")
                print(f"🚗 Trips analyzed: {fuel_data.get('trips_analyzed', 0)}")
            else:
                self.print_error(f"API returned error: {data.get('error')}")
        else:
            self.print_error(f"Request failed: {status_code}")
            print(f"Error: {data}")

    def test_trips_detailed(self):
        """Тест детальной информации о рейсах"""
        self.print_header("ТЕСТ ДЕТАЛЬНОЙ ИНФОРМАЦИИ О РЕЙСАХ")

        params = {
            'vehicle_id': self.test_vehicle_id,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        success, data, status_code = self.test_endpoint('/api/vehicle-trips-detailed/', params)

        if success:
            if data.get('success'):
                trips_data = data.get('data', {})
                self.print_success("Trips detailed completed")

                print(f"🚗 Vehicle: {trips_data.get('vehicle_id')}")
                print(f"📊 Total trips: {trips_data.get('trips_count', 0)}")
                print(f"📏 Total distance: {trips_data.get('total_distance', 0)} km")
                print(f"⛽ Total fuel: {trips_data.get('total_fuel', 0)} L")

                trips = trips_data.get('trips', [])
                if trips:
                    print(f"\n📋 First trip details:")
                    first_trip = trips[0]
                    print(f"  Start: {first_trip.get('start_time')}")
                    print(f"  End: {first_trip.get('end_time')}")
                    print(f"  Distance: {first_trip.get('distance')} km")
                    print(f"  Fuel: {first_trip.get('fuel_consumption')} L")
            else:
                self.print_error(f"API returned error: {data.get('error')}")
        else:
            self.print_error(f"Request failed: {status_code}")
            print(f"Error: {data}")

    def test_enhanced_analytics(self):
        """Тест расширенной аналитики"""
        self.print_header("ТЕСТ РАСШИРЕННОЙ АНАЛИТИКИ")

        params = {
            'vehicle_ids': self.test_vehicle_id,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

        success, data, status_code = self.test_endpoint('/api/enhanced-analytics/', params)

        if success:
            if data.get('success'):
                analytics_data = data.get('data', {})
                self.print_success("Enhanced analytics completed")

                vehicle_metrics = analytics_data.get('vehicle_metrics', {})
                fleet_efficiency = analytics_data.get('fleet_efficiency', {})

                print(f"🚗 Vehicles analyzed: {len(vehicle_metrics)}")
                print(f"📊 Fleet efficiency: {fleet_efficiency.get('avg_fuel_efficiency', 0)} L/100km")
                print(f"📏 Total fleet distance: {fleet_efficiency.get('total_distance', 0)} km")
            else:
                self.print_error(f"API returned error: {data.get('error')}")
        else:
            self.print_error(f"Request failed: {status_code}")
            print(f"Error: {data}")

    def test_debug_api(self):
        """Тест отладочного API"""
        self.print_header("ТЕСТ ОТЛАДОЧНОГО API")

        params = {
            'vehicle_id': self.test_vehicle_id,
            'start_date': f"{self.today.strftime('%Y%m%d')}-0000",
            'end_date': f"{self.today.strftime('%Y%m%d')}-2359"
        }

        success, data, status_code = self.test_endpoint('/api/debug/', params)

        if success:
            self.print_success("Debug API completed")
            print(f"📋 Result keys: {list(data.keys()) if data else 'No data'}")
        else:
            self.print_error(f"Debug API failed: {status_code}")
            print(f"Error: {data}")

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ API")
        print(f"📅 Период тестирования: {self.start_date} - {self.end_date}")
        print(f"🚗 Тестовое ТС: {self.test_vehicle_id}")

        tests = [
            self.test_health_check,
            self.test_enhanced_summary,
            self.test_work_analysis,
            self.test_fuel_analysis,
            self.test_trips_detailed,
            self.test_enhanced_analytics,
            self.test_debug_api
        ]

        results = []
        for test in tests:
            try:
                test()
                results.append(True)
            except Exception as e:
                self.print_error(f"Test {test.__name__} crashed: {e}")
                results.append(False)

        # Сводка
        self.print_header("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        passed = sum(results)
        total = len(results)
        print(f"📊 Пройдено тестов: {passed}/{total}")
        print(f"🎯 Успешность: {passed / total * 100:.1f}%")

        if passed == total:
            print("🎉 Все тесты прошли успешно!")
        else:
            print("⚠️  Некоторые тесты не прошли")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()