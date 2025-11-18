# vehicles/services.py
import requests
import logging
import re
from django.conf import settings
from datetime import datetime, timedelta
import json
import uuid
import math

logger = logging.getLogger(__name__)


class AutoGraphService:
    def __init__(self):
        self.base_url = settings.AUTOGRAPH_API_BASE_URL
        self.session = requests.Session()
        self.token = None

    def login(self, username, password):
        """Аутентификация в AutoGRAPH"""
        try:
            url = f"{self.base_url}/ServiceJSON/Login"
            params = {
                'UserName': username,
                'Password': password,
                'UTCOffset': 180  # Moscow UTC+3
            }

            logger.info(f"🔄 Logging in to AutoGRAPH: {username}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                self.token = response.text.strip('"')
                if self.token and self.token != '""':
                    logger.info(f"✅ Login successful, token: {self.token[:20]}...")
                    return True
                else:
                    logger.error("❌ Invalid credentials - empty token")
                    return False
            elif response.status_code == 401:
                logger.error("❌ Authentication failed - 401 Unauthorized")
                return False
            else:
                logger.error(f"❌ Login failed with status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False

    def get_schemas(self):
        """Получение списка схем"""
        if not self.token:
            logger.error("No token available")
            return []

        try:
            url = f"{self.base_url}/ServiceJSON/EnumSchemas"
            params = {'session': self.token}

            logger.info("🔄 Fetching schemas...")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                schemas = response.json()
                logger.info(f"✅ Got {len(schemas) if isinstance(schemas, list) else 0} schemas")
                return schemas
            else:
                logger.error(f"❌ Failed to get schemas: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error getting schemas: {e}")
            return []

    def get_vehicles(self, schema_id):
        """Получение списка ТС в схеме"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumDevices"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            logger.info(f"🔄 Fetching vehicles for schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got vehicles data, items: {len(data.get('Items', []))}")
                return data
            else:
                logger.error(f"❌ Failed to get vehicles: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting vehicles: {e}")
            return {}

    def get_drivers(self, schema_id):
        """Получение списка водителей"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumDrivers"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            logger.info(f"🔄 Fetching drivers for schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got drivers data")
                return data
            else:
                logger.error(f"❌ Failed to get drivers: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting drivers: {e}")
            return {}

    def get_geofences(self, schema_id):
        """Получение списка геозон"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumGeoFences"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            logger.info(f"🔄 Fetching geofences for schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got geofences data")
                return data
            else:
                logger.error(f"❌ Failed to get geofences: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting geofences: {e}")
            return {}

    def get_parameters(self, schema_id, device_ids):
        """Получение параметров приборов"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumDesignerParameters"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_ids
            }

            logger.info(f"🔄 Fetching parameters for devices: {device_ids}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got parameters data")
                return data
            else:
                logger.error(f"❌ Failed to get parameters: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting parameters: {e}")
            return {}

    def get_statuses(self, schema_id):
        """Получение списка статусов"""
        if not self.token:
            return []

        try:
            url = f"{self.base_url}/ServiceJSON/EnumStatuses"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            logger.info(f"🔄 Fetching statuses for schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got statuses data")
                return data
            else:
                logger.error(f"❌ Failed to get statuses: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error getting statuses: {e}")
            return []

    def get_online_info(self, schema_id, device_ids, final_params=None, include_mchp=False):
        """Получение онлайн информации о ТС"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_ids
            }

            if final_params:
                params['finalParams'] = final_params

            if include_mchp:
                params['mchp'] = '1'

            logger.info(f"🔄 Fetching online info for devices: {device_ids}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got online info")
                return data
            else:
                logger.error(f"❌ Failed to get online info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting online info: {e}")
            return {}

    def get_online_info_all(self, schema_id, final_params=None, include_mchp=False):
        """Получение онлайн информации о всех ТС"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfoAll"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            if final_params:
                params['finalParams'] = final_params

            if include_mchp:
                params['mchp'] = '1'

            logger.info(f"🔄 Fetching online info for all devices in schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got online info for all devices")
                return data
            else:
                logger.error(f"❌ Failed to get online info all: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting online info all: {e}")
            return {}

    def get_track_data(self, schema_id, device_ids, start_date, end_date, trip_splitter_index=-1):
        """Получение трека ТС за период - ФОРМАТ yyyyMMdd-HHmm"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetTrack"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_ids,
                'SD': start_date,  # yyyyMMdd-HHmm
                'ED': end_date,  # yyyyMMdd-HHmm
                'tripSplitterIndex': trip_splitter_index
            }

            logger.info(f"🔄 Getting track for {device_ids} from {start_date} to {end_date}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got track data for {device_ids}")
                return data
            else:
                logger.error(f"❌ Failed to get track: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting track data: {e}")
            return {}

    def get_trips_total(self, schema_id, device_ids, start_date, end_date, trip_splitter_index=0,
                        trip_params=None, trip_total_params=None):
        """Получение информации о рейсах (только итоговые данные) - ФОРМАТ yyyyMMdd-HHmm"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetTripsTotal"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_ids,
                'SD': start_date,  # yyyyMMdd-HHmm
                'ED': end_date,  # yyyyMMdd-HHmm
                'tripSplitterIndex': trip_splitter_index
            }

            if trip_params:
                params['tripParams'] = trip_params
            if trip_total_params:
                params['tripTotalParams'] = trip_total_params

            logger.info(f"🔄 Getting trips total for {device_ids} from {start_date} to {end_date}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got trips total data")
                return data
            else:
                logger.error(f"❌ Failed to get trips total: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting trips total: {e}")
            return {}

    def format_date_for_api(self, date_string, is_start=True):
        """Форматирование даты для API AutoGRAPH в формате yyyyMMdd-HHmm"""
        try:
            logger.info(f"📅 Formatting date: {date_string} (is_start: {is_start})")

            # Если пришла дата с временем (2024-01-01T00:00:00)
            if 'T' in date_string:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.strftime('%Y%m%d-%H%M')

            # Если пришла только дата (2024-01-01) - добавляем время
            elif '-' in date_string and len(date_string) == 10:
                date_part = date_string.replace('-', '')
                if is_start:
                    return f"{date_part}-0000"  # начало дня
                else:
                    return f"{date_part}-2359"  # конец дня

            # Если пришла дата и время (2024-01-01 10:30)
            elif ' ' in date_string:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M')
                return dt.strftime('%Y%m%d-%H%M')

            # Если уже в правильном формате yyyyMMdd-HHmm
            elif len(date_string) == 13 and '-' in date_string and date_string[8] == '-':
                return date_string

            # Если в формате yyyyMMdd (без времени)
            elif len(date_string) == 8 and date_string.isdigit():
                if is_start:
                    return f"{date_string}-0000"
                else:
                    return f"{date_string}-2359"

            else:
                # Пробуем распарсить любую дату
                dt = datetime.fromisoformat(date_string.split('T')[0])
                if is_start:
                    return dt.strftime('%Y%m%d-0000')
                else:
                    return dt.strftime('%Y%m%d-2359')

        except Exception as e:
            logger.error(f"❌ Error formatting date {date_string}: {e}")
            # Fallback - возвращаем сегодняшнюю дату
            today = datetime.now().strftime('%Y%m%d')
            if is_start:
                return f"{today}-0000"
            else:
                return f"{today}-2359"

    def _extract_license_plate_from_name(self, name):
        """Извлечение госномера из имени ТС"""
        try:
            if not name:
                return None

            patterns = [
                r'(\d{3}\s*[A-ZА-Я]{2}\s*\d{2,3})',
                r'([A-ZА-Я]{1,2}\s*\d{3,4}\s*[A-ZА-Я]{1,2})',
                r'(\d{2,3}\s*[A-ZА-Я]{1,2}\s*\d{2,3})',
                r'([A-ZА-Я]{2}\s*\d{3})',
                r'(\d{3}\s*[A-ZА-Я]{2})',
            ]

            for pattern in patterns:
                match = re.search(pattern, name.upper())
                if match:
                    license_plate = match.group(1).strip()
                    if len(license_plate) >= 5:
                        return license_plate

            return None

        except Exception as e:
            logger.error(f"❌ Error extracting license plate from name: {e}")
            return None

    def extract_license_plate_enhanced(self, vehicle_data):
        """УЛУЧШЕННОЕ извлечение госномера"""
        try:
            vehicle_name = vehicle_data.get('Name', '')

            # Пробуем извлечь из свойств vehicle_data
            properties = vehicle_data.get('Properties', [])
            for prop in properties:
                if prop.get('Name') in ['VehicleRegNumber', 'LicensePlate', 'Госномер']:
                    value = prop.get('Value', '')
                    if value and isinstance(value, str) and value.strip():
                        license_plate = value.strip()
                        logger.info(f"✅ Found license plate in properties: {license_plate}")
                        return license_plate

            # Пробуем извлечь из имени ТС (fallback)
            if vehicle_name:
                license_plate = self._extract_license_plate_from_name(vehicle_name)
                if license_plate:
                    logger.info(f"✅ Extracted license plate from name: {license_plate}")
                    return license_plate

            logger.warning(f"⚠️ No license plate found for vehicle: {vehicle_name}")
            return vehicle_name

        except Exception as e:
            logger.error(f"❌ Error in enhanced license plate extraction: {e}")
            return vehicle_data.get('Name', '')

    def test_historical_data_connection(self, schema_id, vehicle_id, start_date, end_date):
        """Тестирование подключения для получения исторических данных - ФОРМАТ yyyyMMdd-HHmm"""
        try:
            logger.info(f"🔍 Testing historical data connection for {vehicle_id}")

            # Форматирование дат с временем
            start_fmt = self.format_date_for_api(start_date, is_start=True)
            end_fmt = self.format_date_for_api(end_date, is_start=False)

            logger.info(f"📅 Testing period: {start_fmt} to {end_fmt}")

            # Пробуем разные методы API для получения исторических данных
            test_results = {}

            # 1. GetTripsTotal
            logger.info("🔄 Testing GetTripsTotal...")
            trips_total = self.get_trips_total(schema_id, vehicle_id, start_fmt, end_fmt)
            test_results['get_trips_total'] = {
                'success': bool(trips_total),
                'has_vehicle_data': vehicle_id in trips_total if trips_total else False,
                'data_structure': list(trips_total.keys()) if trips_total else None
            }

            # 2. GetTrack
            logger.info("🔄 Testing GetTrack...")
            track_data = self.get_track_data(schema_id, vehicle_id, start_fmt, end_fmt)
            test_results['get_track'] = {
                'success': bool(track_data),
                'has_vehicle_data': vehicle_id in track_data if track_data else False,
                'data_points': len(track_data.get(vehicle_id, [])) if track_data else 0
            }

            # 3. GetOnlineInfo (для проверки текущего состояния)
            logger.info("🔄 Testing GetOnlineInfo...")
            online_info = self.get_online_info(schema_id, vehicle_id)
            test_results['get_online_info'] = {
                'success': bool(online_info),
                'has_vehicle_data': vehicle_id in online_info if online_info else False,
                'last_update': online_info.get(vehicle_id, {}).get('_LastDataLocal') if online_info else None
            }

            return test_results

        except Exception as e:
            logger.error(f"❌ Error testing historical data connection: {e}")
            return {'error': str(e)}

    def get_vehicle_detailed_info(self, schema_id, vehicle_id):
        """Получение детальной информации о ТС для диагностики"""
        try:
            logger.info(f"🔍 Getting detailed info for vehicle: {vehicle_id}")

            # Получаем базовую информацию о ТС
            vehicles_data = self.get_vehicles(schema_id)
            vehicle_info = None

            if vehicles_data and 'Items' in vehicles_data:
                for vehicle in vehicles_data['Items']:
                    if str(vehicle.get('ID')) == vehicle_id:
                        vehicle_info = vehicle
                        break

            if not vehicle_info:
                return {'error': 'Vehicle not found'}

            # Получаем онлайн информацию
            online_info = self.get_online_info(schema_id, vehicle_id)
            online_data = online_info.get(vehicle_id, {}) if online_info else {}

            # Форматируем информацию для отображения
            detailed_info = {
                'basic_info': {
                    'id': vehicle_info.get('ID'),
                    'name': vehicle_info.get('Name'),
                    'serial': vehicle_info.get('Serial'),
                    'license_plate': self.extract_license_plate_enhanced(vehicle_info),
                    'properties': vehicle_info.get('Properties', [])
                },
                'online_info': {
                    'last_update': online_data.get('_LastDataLocal'),
                    'last_coords': online_data.get('_LastCoordsLocal'),
                    'speed': online_data.get('Speed'),
                    'address': online_data.get('Address'),
                    'final_params': online_data.get('Final', {})
                },
                'trip_splitters': vehicle_info.get('TripSplitters', [])
            }

            return detailed_info

        except Exception as e:
            logger.error(f"❌ Error getting vehicle detailed info: {e}")
            return {'error': str(e)}


class AutoGraphHistoricalService:
    def __init__(self):
        self.base_service = AutoGraphService()
        logger.info("🔄 AutoGraphHistoricalService initialized")

    def get_vehicle_historical_statistics(self, username, password, vehicle_id, schema_id, start_date, end_date):
        """УЛУЧШЕННОЕ получение реальных исторических данных по ТС - ФОРМАТ yyyyMMdd-HHmm"""
        try:
            logger.info(f"🔄 Getting historical data for {vehicle_id} from {start_date} to {end_date}")

            # Аутентификация с переданными учетными данными
            if not self.base_service.login(username, password):
                logger.error("❌ Authentication failed")
                return self._create_empty_response(vehicle_id)

            # Форматирование дат для API - С ВРЕМЕНЕМ
            start_date_fmt = self.base_service.format_date_for_api(start_date, is_start=True)
            end_date_fmt = self.base_service.format_date_for_api(end_date, is_start=False)

            logger.info(f"📅 Formatted dates for API: {start_date_fmt} to {end_date_fmt}")

            # Пробуем разные методы получения данных
            historical_data = self._get_historical_data_multiple_methods(
                schema_id, vehicle_id, start_date_fmt, end_date_fmt
            )

            if historical_data:
                logger.info(f"✅ Successfully got historical data for {vehicle_id}")
                return historical_data
            else:
                logger.warning(f"⚠️ No historical data found for {vehicle_id}")
                return self._create_vehicle_info_with_online_data(vehicle_id, schema_id)

        except Exception as e:
            logger.error(f"❌ Error getting historical statistics: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return self._create_empty_response(vehicle_id)

    def _get_historical_data_multiple_methods(self, schema_id, vehicle_id, start_date_fmt, end_date_fmt):
        """Пробуем несколько методов получения исторических данных"""

        # 1. Пробуем GetTripsTotal с разными tripSplitterIndex
        for trip_splitter_index in [0, 1, -1]:
            try:
                logger.info(f"🔄 Trying GetTripsTotal with splitter index: {trip_splitter_index}")
                trips_data = self.base_service.get_trips_total(
                    schema_id, vehicle_id, start_date_fmt, end_date_fmt, trip_splitter_index
                )

                if trips_data and vehicle_id in trips_data:
                    vehicle_data = trips_data[vehicle_id]
                    trips = vehicle_data.get('Trips', [])
                    total_data = vehicle_data.get('Total', {})

                    logger.info(f"📊 Found {len(trips)} trips with splitter {trip_splitter_index}")

                    if trips:
                        result = self._transform_historical_data_with_trips(vehicle_data, vehicle_id)
                        result['trip_splitter_index'] = trip_splitter_index
                        return result
                    elif total_data:
                        result = self._transform_historical_data_from_total(vehicle_data, vehicle_id)
                        result['trip_splitter_index'] = trip_splitter_index
                        return result

            except Exception as e:
                logger.error(f"❌ Error with splitter {trip_splitter_index}: {e}")
                continue

        # 2. Пробуем GetTrack для получения трека
        try:
            logger.info("🔄 Trying GetTrack as fallback...")
            track_data = self.base_service.get_track_data(schema_id, vehicle_id, start_date_fmt, end_date_fmt)

            if track_data and vehicle_id in track_data:
                track_points = track_data[vehicle_id]
                if track_points:
                    logger.info(f"📊 Found {len(track_points)} track points")
                    return self._transform_track_data_to_statistics(track_points, vehicle_id)

        except Exception as e:
            logger.error(f"❌ Error getting track data: {e}")

        return None

    def _transform_track_data_to_statistics(self, track_points, vehicle_id):
        """Преобразование данных трека в статистику"""
        try:
            if not track_points:
                return None

            # Анализируем точки трека
            total_distance = 0
            speeds = []
            timestamps = []

            for i in range(1, len(track_points)):
                point1 = track_points[i - 1]
                point2 = track_points[i]

                # Рассчитываем расстояние между точками (упрощенно)
                if 'Lat' in point1 and 'Lng' in point1 and 'Lat' in point2 and 'Lng' in point2:
                    # Простая аппроксимация расстояния
                    distance = self._calculate_distance(
                        point1['Lat'], point1['Lng'],
                        point2['Lat'], point2['Lng']
                    )
                    total_distance += distance

                # Собираем скорости
                if 'Speed' in point2:
                    speeds.append(point2['Speed'])

                # Собираем временные метки
                if '_SD' in point2:
                    timestamps.append(point2['_SD'])

            # Рассчитываем статистику
            statistics = {
                'total_distance': round(total_distance, 2),
                'max_speed': round(max(speeds) if speeds else 0, 2),
                'average_speed': round(sum(speeds) / len(speeds) if speeds else 0, 2),
                'data_points_count': len(track_points),
            }

            return {
                'summary': statistics,
                'fuel_analytics': {},
                'violations': {},
                'equipment_status': {},
                'location': {},
                'time_series': [],
                'vehicle_id': vehicle_id,
                'vehicle_name': 'From Track Data',
                'license_plate': 'Unknown',
                'data_source': 'autograph_track_data',
                'trips_count': 0,
                'transformation_success': True,
                'note': f'Данные из трека ({len(track_points)} точек)'
            }

        except Exception as e:
            logger.error(f"❌ Error transforming track data: {e}")
            return None

    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """Упрощенный расчет расстояния между точками"""
        # Простая аппроксимация - в реальности нужно использовать формулу Хаверсина
        return abs(lat1 - lat2) * 111000 + abs(lng1 - lng2) * 111000  # примерные метры

    def _create_vehicle_info_with_online_data(self, vehicle_id, schema_id):
        """Создание информации о ТС с онлайн-данными"""
        try:
            # Получаем онлайн-данные как fallback
            online_info = self.base_service.get_online_info(schema_id, vehicle_id)
            online_data = online_info.get(vehicle_id, {}) if online_info else {}

            return {
                'summary': {
                    'total_distance': 0,
                    'total_fuel_consumption': 0,
                    'total_engine_hours': '00:00:00',
                    'max_speed': online_data.get('Speed', 0),
                    'average_speed': 0,
                },
                'fuel_analytics': {
                    'current_level': online_data.get('TankMainFuelLevel Last', 0),
                },
                'violations': {},
                'equipment_status': {
                    'ignition': online_data.get('DIgnition Last', False),
                    'gsm_signal': online_data.get('DGSMAvailable Last', False),
                    'gps_signal': online_data.get('DGPSAvailable Last', False),
                    'movement': self._get_movement_status(online_data.get('Motion Last', 1))
                },
                'location': {
                    'address': online_data.get('Address', 'Не определено'),
                    'coordinates': {
                        'lat': online_data.get('_LastCoordsLocal', {}).get('Lat', 0),
                        'lng': online_data.get('_LastCoordsLocal', {}).get('Lng', 0)
                    },
                    'last_update': online_data.get('_LastDataLocal', '')
                },
                'time_series': [],
                'vehicle_id': vehicle_id,
                'vehicle_name': 'Online Data Only',
                'license_plate': 'Unknown',
                'data_source': 'autograph_online_only',
                'trips_count': 0,
                'transformation_success': True,
                'note': 'Только онлайн-данные (исторические данные не найдены)'
            }

        except Exception as e:
            logger.error(f"❌ Error creating online data response: {e}")
            return self._create_empty_response(vehicle_id)

    def _transform_historical_data_with_trips(self, raw_data, vehicle_id):
        """Преобразование данных когда есть рейсы"""
        try:
            logger.info(f"🔄 Transforming historical data with trips for {vehicle_id}")

            trips = raw_data.get('Trips', [])
            if not trips:
                logger.warning(f"⚠️ No trips in transform_historical_data_with_trips for {vehicle_id}")
                return self._transform_historical_data_from_total(raw_data, vehicle_id)

            logger.info(f"📊 Processing {len(trips)} trips")

            # АГРЕГИРУЕМ данные по ВСЕМ рейсам
            total_stats = self._aggregate_trips_data(trips)

            # Берем данные из последнего рейса для текущих показателей
            last_trip = trips[-1]
            last_total = last_trip.get('Total', {})

            # Основная статистика
            statistics = {
                'total_distance': round(total_stats['distance'], 2),
                'total_fuel_consumption': round(total_stats['fuel_consumption'], 2),
                'total_engine_hours': self._format_duration(total_stats['engine_hours']),
                'total_move_duration': self._format_duration(total_stats['move_duration']),
                'total_park_duration': self._format_duration(total_stats['park_duration']),
                'max_speed': round(total_stats['max_speed'], 2),
                'average_speed': round(total_stats['average_speed'], 2),
                'fuel_efficiency': round(total_stats['fuel_efficiency'], 2),
                'parking_count': total_stats['parking_count'],
                'overspeed_count': total_stats['overspeed_count'],
            }

            # Топливная аналитика (из последнего рейса)
            fuel_analytics = {
                'current_level': round(last_total.get('TankMainFuelLevel Last', 0), 2),
                'refills_count': last_total.get('TankMainFuelUpCount', 0),
                'refills_volume': round(last_total.get('TankMainFuelUpVol Diff', 0), 2),
                'consumption_per_motor_hour': round(last_total.get('Engine1FuelConsumMPerMH', 0), 2),
                'total_fuel_volume': round(
                    last_total.get('TankMainFuelLevel Last', 0) + last_total.get('TankMainFuelUpVol Diff', 0), 2),
            }

            # Нарушения (суммируем по всем рейсам)
            violations = {
                'overspeed_duration': self._format_duration(total_stats['overspeed_duration']),
                'penalty_points': round(total_stats['penalty_points'], 2),
                'overspeed_points': round(total_stats['overspeed_points'], 2),
            }

            # Статусы оборудования (из последнего рейса)
            equipment_status = {
                'ignition': last_total.get('DIgnition Last', False),
                'gsm_signal': last_total.get('DGSMAvailable Last', False),
                'gps_signal': last_total.get('DGPSAvailable Last', False),
                'power': last_total.get('Power Last', False),
                'movement': self._get_movement_status(last_total.get('Motion Last', 1))
            }

            # Локация (из последнего рейса)
            location = {
                'address': last_total.get('CurrLocation', 'Не определено'),
                'coordinates': {
                    'lat': last_trip.get('PointEnd', {}).get('Lat', 0),
                    'lng': last_trip.get('PointEnd', {}).get('Lng', 0)
                },
                'last_update': raw_data.get('_LastDataLocal', '')
            }

            # Генерация временных рядов для графиков
            time_series = self._generate_time_series_from_trips(trips)

            result = {
                'summary': statistics,
                'fuel_analytics': fuel_analytics,
                'violations': violations,
                'equipment_status': equipment_status,
                'location': location,
                'time_series': time_series,
                'vehicle_id': vehicle_id,
                'vehicle_name': raw_data.get('Name', ''),
                'license_plate': raw_data.get('VRN', ''),
                'data_source': 'autograph_real_trips',
                'period': {
                    'start': trips[0].get('SD') if trips else '',
                    'end': trips[-1].get('ED') if trips else ''
                },
                'trips_count': len(trips),
                'transformation_success': True
            }

            logger.info(f"✅ Successfully transformed historical data with trips for {vehicle_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Error transforming trips data: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            # Fallback to Total data transformation
            return self._transform_historical_data_from_total(raw_data, vehicle_id)

    def _transform_historical_data_from_total(self, raw_data, vehicle_id):
        """Преобразование данных из Total когда нет рейсов"""
        try:
            logger.info(f"🔄 Transforming historical data from Total for {vehicle_id}")

            total_data = raw_data.get('Total', {})
            logger.info(f"📊 Total data keys available: {list(total_data.keys())[:15]}")

            # Основная статистика из Total
            statistics = {
                'total_distance': round(total_data.get('TotalDistance', 0), 2),
                'max_speed': round(total_data.get('MaxSpeed', 0), 2),
                'parking_count': total_data.get('ParkCount', 0),
                'overspeed_count': total_data.get('OverspeedCount', 0),
            }

            # Добавляем дополнительные поля если они есть
            if 'Engine1FuelConsum' in total_data:
                statistics['total_fuel_consumption'] = round(total_data.get('Engine1FuelConsum', 0), 2)

            if 'Engine1Motohours' in total_data:
                statistics['total_engine_hours'] = total_data.get('Engine1Motohours', '00:00:00')

            # Топливная аналитика
            fuel_analytics = {
                'current_level': round(total_data.get('TankMainFuelLevel Last', 0), 2),
                'total_fuel_volume': round(
                    total_data.get('TankMainFuelLevel Last', 0) + total_data.get('Engine1FuelConsum', 0), 2),
            }

            # Добавляем дополнительные поля топлива если они есть
            if 'TankMainFuelUpCount' in total_data:
                fuel_analytics['refills_count'] = total_data.get('TankMainFuelUpCount', 0)

            if 'TankMainFuelUpVol Diff' in total_data:
                fuel_analytics['refills_volume'] = round(total_data.get('TankMainFuelUpVol Diff', 0), 2)

            # Нарушения
            violations = {
                'overspeed_points': round(total_data.get('DQOverspeedPoints Diff', 0), 2),
                'penalty_points': round(total_data.get('DQPoints Diff', 0), 2),
            }

            # Статусы оборудования
            equipment_status = {
                'ignition': total_data.get('DIgnition Last', False),
                'gsm_signal': total_data.get('DGSMAvailable Last', False),
                'gps_signal': total_data.get('DGPSAvailable Last', False),
                'power': total_data.get('Power Last', False),
                'movement': self._get_movement_status(total_data.get('Motion Last', 1))
            }

            # Локация
            location = {
                'address': total_data.get('CurrLocation', 'Не определено'),
                'coordinates': {
                    'lat': raw_data.get('LastPosition', {}).get('Lat', 0),
                    'lng': raw_data.get('LastPosition', {}).get('Lng', 0)
                },
                'last_update': raw_data.get('_LastDataLocal', '')
            }

            result = {
                'summary': statistics,
                'fuel_analytics': fuel_analytics,
                'violations': violations,
                'equipment_status': equipment_status,
                'location': location,
                'time_series': [],  # Нет временных рядов без рейсов
                'vehicle_id': vehicle_id,
                'vehicle_name': raw_data.get('Name', ''),
                'license_plate': raw_data.get('VRN', ''),
                'data_source': 'autograph_total_only',
                'trips_count': 0,
                'transformation_success': True,
                'note': 'Данные получены из Total (рейсов нет за указанный период)'
            }

            logger.info(f"✅ Successfully transformed Total data for {vehicle_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Error transforming Total data: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return self._create_vehicle_info_response(raw_data, vehicle_id)

    def _create_empty_response(self, vehicle_id):
        """Создает пустой ответ с базовой структурой"""
        return {
            'summary': {},
            'fuel_analytics': {},
            'violations': {},
            'equipment_status': {},
            'location': {},
            'time_series': [],
            'vehicle_id': vehicle_id,
            'vehicle_name': 'Unknown',
            'license_plate': 'Unknown',
            'data_source': 'autograph_empty',
            'trips_count': 0,
            'transformation_success': False,
            'note': 'Нет данных от API'
        }

    def _create_vehicle_info_response(self, vehicle_data, vehicle_id):
        """Создает ответ с базовой информацией о ТС"""
        return {
            'summary': {},
            'fuel_analytics': {},
            'violations': {},
            'equipment_status': {},
            'location': {},
            'time_series': [],
            'vehicle_id': vehicle_id,
            'vehicle_name': vehicle_data.get('Name', 'Unknown'),
            'license_plate': vehicle_data.get('VRN', 'Unknown'),
            'data_source': 'autograph_basic',
            'trips_count': 0,
            'transformation_success': False,
            'note': 'Только базовая информация о ТС'
        }

    def _aggregate_trips_data(self, trips):
        """Агрегирует данные по всем рейсам"""
        total_distance = 0
        total_fuel_consumption = 0
        total_engine_hours = 0
        total_move_duration = 0
        total_park_duration = 0
        max_speed = 0
        total_parking_count = 0
        total_overspeed_count = 0
        total_overspeed_duration = 0
        total_penalty_points = 0
        total_overspeed_points = 0

        for trip in trips:
            total = trip.get('Total', {})

            # Суммируем основные показатели
            total_distance += total.get('TotalDistance', 0)
            total_fuel_consumption += total.get('Engine1FuelConsum', 0)
            total_parking_count += total.get('ParkCount', 0)
            total_overspeed_count += total.get('OverspeedCount', 0)

            # Находим максимальную скорость
            trip_max_speed = total.get('MaxSpeed', 0)
            if trip_max_speed > max_speed:
                max_speed = trip_max_speed

            # Обрабатываем время
            engine_hours = self._parse_duration(total.get('Engine1Motohours', '00:00:00'))
            move_duration = self._parse_duration(total.get('MoveDuration', '00:00:00'))
            park_duration = self._parse_duration(total.get('ParkDuration', '00:00:00'))

            total_engine_hours += engine_hours
            total_move_duration += move_duration
            total_park_duration += park_duration

            # Нарушения
            overspeed_duration = self._find_overspeed_duration(trip.get('Stages', []))
            total_overspeed_duration += self._parse_duration(overspeed_duration)
            total_penalty_points += total.get('DQPoints Diff', 0)
            total_overspeed_points += total.get('DQOverspeedPoints Diff', 0)

        # Рассчитываем среднюю скорость
        average_speed = 0
        if total_move_duration > 0 and total_distance > 0:
            average_speed = total_distance / (total_move_duration / 3600)

        # Рассчитываем расход топлива на 100км
        fuel_efficiency = 0
        if total_distance > 0:
            fuel_efficiency = (total_fuel_consumption / total_distance) * 100

        return {
            'distance': total_distance,
            'fuel_consumption': total_fuel_consumption,
            'engine_hours': total_engine_hours,
            'move_duration': total_move_duration,
            'park_duration': total_park_duration,
            'max_speed': max_speed,
            'average_speed': average_speed,
            'fuel_efficiency': fuel_efficiency,
            'parking_count': total_parking_count,
            'overspeed_count': total_overspeed_count,
            'overspeed_duration': total_overspeed_duration,
            'penalty_points': total_penalty_points,
            'overspeed_points': total_overspeed_points,
        }

    def _parse_duration(self, duration_str):
        """Парсит строку длительности в секунды"""
        try:
            if not duration_str:
                return 0

            # Если это уже число, возвращаем как есть
            if isinstance(duration_str, (int, float)):
                return duration_str

            # Парсим формат HH:MM:SS
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            else:
                return 0
        except:
            return 0

    def _format_duration(self, total_seconds):
        """Форматирует секунды в строку HH:MM:SS"""
        try:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"

    def _find_overspeed_duration(self, stages):
        """Находит длительность превышений скорости"""
        for stage in stages:
            if stage.get('Name') == 'Overspeed':
                return stage.get('Total', {}).get('TotalDuration', '00:00:00')
        return '00:00:00'

    def _get_movement_status(self, motion_code):
        """Преобразует код движения в текст"""
        motion_map = {1: 'parking', 2: 'moving', 3: 'flying'}
        return motion_map.get(motion_code, 'unknown')

    def _generate_time_series_from_trips(self, trips):
        """Генерация временных рядов из данных рейсов"""
        time_series = []

        for trip in trips:
            total = trip.get('Total', {})
            timestamp = trip.get('_SD')  # Время начала рейса

            time_series.append({
                'timestamp': timestamp,
                'distance': round(total.get('TotalDistance', 0), 2),
                'fuel_consumption': round(total.get('Engine1FuelConsum', 0), 2),
                'max_speed': round(total.get('MaxSpeed', 0), 2),
            })

        return time_series


class AutoGraphDataCollector:
    """Класс для сбора всех возможных данных из AutoGRAPH API"""

    def __init__(self):
        self.service = AutoGraphService()
        self.collected_data = {}

    def collect_all_data(self, username, password, schema_id, start_date=None, end_date=None):
        """Сбор всех доступных данных для схемы - ФОРМАТ yyyyMMdd-HHmm"""
        try:
            logger.info(f"🔄 Starting comprehensive data collection for schema: {schema_id}")

            # Аутентификация с переданными учетными данными
            if not self.service.login(username, password):
                logger.error("❌ Authentication failed")
                return None

            # Базовые данные схемы
            self.collected_data['schemas'] = self.service.get_schemas()

            # Получаем список ТС
            vehicles_data = self.service.get_vehicles(schema_id)
            self.collected_data['vehicles'] = vehicles_data

            if not vehicles_data or 'Items' not in vehicles_data:
                logger.error("❌ No vehicles found")
                return self.collected_data

            # Извлекаем ID всех ТС
            vehicle_ids = [vehicle['ID'] for vehicle in vehicles_data['Items']]
            vehicle_ids_str = ','.join(vehicle_ids[:5])  # Берем первые 5 для теста

            # Собираем все типы данных
            self._collect_basic_data(schema_id, vehicle_ids_str)

            if start_date and end_date:
                self._collect_historical_data(schema_id, vehicle_ids_str, start_date, end_date)

            self._collect_additional_data(schema_id)

            logger.info(f"✅ Comprehensive data collection completed")
            return self.collected_data

        except Exception as e:
            logger.error(f"❌ Error in comprehensive data collection: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            return self.collected_data

    def _collect_basic_data(self, schema_id, vehicle_ids):
        """Сбор базовых данных"""
        try:
            # Основные данные
            self.collected_data['drivers'] = self.service.get_drivers(schema_id)
            self.collected_data['geofences'] = self.service.get_geofences(schema_id)
            self.collected_data['parameters'] = self.service.get_parameters(schema_id, vehicle_ids)
            self.collected_data['statuses'] = self.service.get_statuses(schema_id)
            self.collected_data['online_info'] = self.service.get_online_info(schema_id, vehicle_ids)
            self.collected_data['online_info_all'] = self.service.get_online_info_all(schema_id)

        except Exception as e:
            logger.error(f"❌ Error collecting basic data: {e}")

    def _collect_historical_data(self, schema_id, vehicle_ids, start_date, end_date):
        """Сбор исторических данных - ФОРМАТ yyyyMMdd-HHmm"""
        try:
            # Форматирование дат с временем
            start_fmt = self.service.format_date_for_api(start_date, is_start=True)
            end_fmt = self.service.format_date_for_api(end_date, is_start=False)

            # Исторические данные
            self.collected_data['track_data'] = self.service.get_track_data(
                schema_id, vehicle_ids, start_fmt, end_fmt)

            # Данные по рейсам
            self.collected_data['trips_total'] = self.service.get_trips_total(
                schema_id, vehicle_ids, start_fmt, end_fmt)

        except Exception as e:
            logger.error(f"❌ Error collecting historical data: {e}")

    def _collect_additional_data(self, schema_id):
        """Сбор дополнительных данных"""
        try:
            # Можно добавить вызовы других методов API
            pass

        except Exception as e:
            logger.error(f"❌ Error collecting additional data: {e}")

    def save_collected_data(self, filename=None):
        """Сохранение собранных данных в файл"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"autograph_data_{timestamp}.json"

            # Сериализуем данные (обрабатываем UUID и другие несериализуемые объекты)
            def serialize_obj(obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                return obj

            serializable_data = json.loads(json.dumps(self.collected_data, default=serialize_obj, indent=2))

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Data saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
            return None