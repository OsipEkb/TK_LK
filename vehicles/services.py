# vehicles/services.py
import requests
import logging
import re
from django.conf import settings
from datetime import datetime, timedelta
import json

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

    def get_trips_total(self, schema_id, device_id, start_date, end_date):
        """Получение суммарных данных по рейсам"""
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/ServiceJSON/GetTripsTotal"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id,
                'SD': start_date,
                'ED': end_date,
                'tripSplitterIndex': 0
            }

            logger.info(f"🔄 Getting trips total for {device_id}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got trips total for {device_id}")
                return data
            else:
                logger.error(f"❌ Failed to get trips total: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting trips total: {e}")
            return None

    def get_track_data(self, schema_id, device_id, start_date, end_date):
        """Получение трека ТС за период"""
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/ServiceJSON/GetTrack"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id,
                'SD': start_date,
                'ED': end_date,
                'tripSplitterIndex': -1
            }

            logger.info(f"🔄 Getting track for {device_id} from {start_date} to {end_date}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got track data for {device_id}")
                return data
            else:
                logger.error(f"❌ Failed to get track: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting track data: {e}")
            return None

    def format_date_for_api(self, date_string, include_time=False):
        """Форматирование даты для API AutoGRAPH"""
        try:
            if include_time:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.strftime('%Y%m%d-%H%M')
            else:
                dt = datetime.fromisoformat(date_string.split('T')[0])
                return dt.strftime('%Y%m%d')
        except Exception as e:
            logger.error(f"❌ Error formatting date: {e}")
            return date_string

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


class AutoGraphHistoricalService:
    def __init__(self):
        self.base_service = AutoGraphService()

    def get_vehicle_historical_statistics(self, vehicle_id, schema_id, start_date, end_date):
        """Получение реальных исторических данных по ТС"""
        try:
            logger.info(f"🔄 Getting historical data for {vehicle_id} from {start_date} to {end_date}")

            # Форматируем даты для API
            start_date_fmt = self.format_date_for_api(start_date)
            end_date_fmt = self.format_date_for_api(end_date)

            # Получаем данные по рейсам
            trips_data = self.base_service.get_trips_total(schema_id, vehicle_id, start_date_fmt, end_date_fmt)

            if not trips_data:
                logger.warning(f"⚠️ No trips data for {vehicle_id}")
                return None

            vehicle_data = trips_data.get(vehicle_id, {})
            if not vehicle_data:
                return None

            return self.transform_historical_data(vehicle_data, vehicle_id)

        except Exception as e:
            logger.error(f"❌ Error getting historical statistics: {e}")
            return None

    def transform_historical_data(self, raw_data, vehicle_id):
        """Преобразование сырых данных в формат для дашборда"""
        try:
            trips = raw_data.get('Trips', [])
            if not trips:
                return None

            # Берем первый рейс (можно агрегировать по всем)
            trip = trips[0]
            total = trip.get('Total', {})

            # Основная статистика
            statistics = {
                'total_distance': round(total.get('TotalDistance', 0), 2),
                'total_fuel_consumption': round(total.get('Engine1FuelConsum', 0), 2),
                'total_engine_hours': total.get('Engine1Motohours', '00:00:00'),
                'total_move_duration': total.get('MoveDuration', '00:00:00'),
                'total_park_duration': total.get('ParkDuration', '00:00:00'),
                'max_speed': round(total.get('MaxSpeed', 0), 2),
                'average_speed': round(total.get('AverageSpeed', 0), 2),
                'fuel_efficiency': round(total.get('Engine1FuelConsumMPer100km', 0), 2),
                'parking_count': total.get('ParkCount', 0),
                'overspeed_count': total.get('OverspeedCount', 0),
            }

            # Топливная аналитика
            fuel_analytics = {
                'current_level': round(total.get('TankMainFuelLevel Last', 0), 2),
                'refills_count': total.get('TankMainFuelUpCount', 0),
                'refills_volume': round(total.get('TankMainFuelUpVol Diff', 0), 2),
                'consumption_per_motor_hour': round(total.get('Engine1FuelConsumMPerMH', 0), 2),
                'total_fuel_volume': round(
                    total.get('TankMainFuelLevel Last', 0) + total.get('TankMainFuelUpVol Diff', 0), 2),
            }

            # Нарушения
            violations = {
                'overspeed_duration': self._find_overspeed_duration(trip.get('Stages', [])),
                'penalty_points': round(total.get('DQPoints Diff', 0), 2),
                'overspeed_points': round(total.get('DQOverspeedPoints Diff', 0), 2),
            }

            # Статусы оборудования
            equipment_status = {
                'ignition': raw_data.get('Total', {}).get('DIgnition Last', False),
                'gsm_signal': raw_data.get('Total', {}).get('DGSMAvailable Last', False),
                'gps_signal': raw_data.get('Total', {}).get('DGPSAvailable Last', False),
                'power': raw_data.get('Total', {}).get('Power Last', False),
                'movement': self._get_movement_status(raw_data.get('Total', {}).get('Motion Last', 1))
            }

            # Локация
            location = {
                'address': raw_data.get('Total', {}).get('CurrLocation', 'Не определено'),
                'coordinates': {
                    'lat': trip.get('PointEnd', {}).get('Lat', 0),
                    'lng': trip.get('PointEnd', {}).get('Lng', 0)
                },
                'last_update': raw_data.get('_LastDataLocal', '')
            }

            # Генерация временных рядов для графиков
            time_series = self.generate_time_series_from_trips(trips)

            return {
                'summary': statistics,
                'fuel_analytics': fuel_analytics,
                'violations': violations,
                'equipment_status': equipment_status,
                'location': location,
                'time_series': time_series,
                'vehicle_id': vehicle_id,
                'vehicle_name': raw_data.get('Name', ''),
                'license_plate': raw_data.get('VRN', ''),
                'data_source': 'autograph_real',
                'period': {
                    'start': trip.get('SD'),
                    'end': trip.get('ED')
                }
            }

        except Exception as e:
            logger.error(f"❌ Error transforming historical data: {e}")
            return None

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

    def generate_time_series_from_trips(self, trips):
        """Генерация временных рядов из данных рейсов"""
        time_series = []

        for trip in trips:
            total = trip.get('Total', {})
            timestamp = trip.get('_SD')  # Время начала рейса

            # Расчет общего объема топлива (текущий уровень + израсходованный)
            current_fuel = total.get('TankMainFuelLevel Last', 0)
            consumed_fuel = total.get('Engine1FuelConsum', 0)
            total_fuel_volume = current_fuel + consumed_fuel

            time_series.append({
                'timestamp': timestamp,
                'distance': round(total.get('TotalDistance', 0), 2),
                'fuel_consumption': round(total.get('Engine1FuelConsum', 0), 2),
                'engine_hours': self.duration_to_hours(total.get('Engine1Motohours', '00:00:00')),
                'move_duration': self.duration_to_hours(total.get('MoveDuration', '00:00:00')),
                'max_speed': round(total.get('MaxSpeed', 0), 2),
                'fuel_level': round(total.get('TankMainFuelLevel Last', 0), 2),
                'total_fuel_volume': round(total_fuel_volume, 2),
            })

        return time_series

    def duration_to_hours(self, duration_str):
        """Конвертирует строку длительности в часы"""
        try:
            if not duration_str:
                return 0
            parts = duration_str.split(':')
            return int(parts[0]) + int(parts[1]) / 60 + int(parts[2]) / 3600
        except:
            return 0

    def format_date_for_api(self, date_string):
        """Форматирование даты для API"""
        from datetime import datetime
        try:
            dt = datetime.strptime(date_string, '%Y-%m-%d')
            return dt.strftime('%Y%m%d')
        except:
            return date_string

    def get_historical_time_series(self, schema_id, vehicle_id, start_date, end_date, parameters):
        """Получение детальных временных рядов для графиков"""
        try:
            if not self.base_service.login("Osipenko", "Osipenko"):
                return None

            start_date_fmt = self.format_date_for_api(start_date)
            end_date_fmt = self.format_date_for_api(end_date)

            # Получаем данные по рейсам
            trips_data = self.base_service.get_trips_total(schema_id, vehicle_id, start_date_fmt, end_date_fmt)

            if not trips_data:
                return self.generate_mock_time_series(start_date, end_date)

            return self.transform_to_time_series(trips_data.get(vehicle_id, {}), parameters)

        except Exception as e:
            logger.error(f"❌ Error getting historical time series: {e}")
            return self.generate_mock_time_series(start_date, end_date)

    def transform_to_time_series(self, vehicle_data, parameters):
        """Трансформация данных в временные ряды"""
        trips = vehicle_data.get('Trips', [])
        time_series = []

        for trip in trips:
            total = trip.get('Total', {})
            point_data = {
                'timestamp': trip.get('_SD'),
                'distance': round(total.get('TotalDistance', 0), 2),
                'fuel_consumption': round(total.get('Engine1FuelConsum', 0), 2),
                'max_speed': round(total.get('MaxSpeed', 0), 2),
                'engine_hours': self.duration_to_hours(total.get('Engine1Motohours', '00:00:00')),
                'fuel_level': round(total.get('TankMainFuelLevel Last', 0), 2),
                'total_fuel_volume': round(total.get('TankMainFuelLevel Last', 0) + total.get('Engine1FuelConsum', 0),
                                           2),
            }
            time_series.append(point_data)

        return time_series

    def generate_mock_time_series(self, start_date, end_date):
        """Генерация тестовых временных рядов"""
        from datetime import datetime, timedelta
        import random

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end - start).days + 1

        time_series = []
        current = start

        for i in range(days_diff * 24):  # Почасовые данные
            time_series.append({
                'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                'distance': round(random.uniform(5, 50), 2),
                'fuel_consumption': round(random.uniform(2, 15), 2),
                'max_speed': round(random.uniform(30, 90), 2),
                'engine_hours': round(random.uniform(0.5, 2.5), 2),
                'fuel_level': round(random.uniform(100, 500), 2),
                'total_fuel_volume': round(random.uniform(200, 600), 2),
            })
            current += timedelta(hours=1)

        return time_series