# dashboard/services.py
import requests
import logging
import re
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
import dateutil.parser

logger = logging.getLogger(__name__)


class AutoGraphDashboardService:
    """Сервис для работы с AutoGRAPH API"""

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
                self.token = response.text.strip()
                if self.token and len(self.token) > 10:
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
                logger.info(f"✅ Got {len(schemas)} schemas")
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

    def get_online_info_all(self, schema_id):
        """Получение информации о последнем местоположении всех устройств"""
        if not self.token:
            logger.error("No token available for online info")
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfoAll"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'finalParams': 'Speed,FuelLevel,EngineHours,Latitude,Longitude,Address,TankMainFuelLevel,FL1,FL2',
                'mchp': '0'
            }

            logger.info(f"🔄 Getting online info for all devices in schema: {schema_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got online info for {len(data)} devices")
                return data
            else:
                logger.error(f"❌ Failed to get online info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting online info: {e}")
            return {}

    def parse_timestamp(self, timestamp):
        """Универсальный парсер временных меток"""
        if not timestamp:
            return None

        try:
            if isinstance(timestamp, (int, float)):
                # Unix timestamp
                if timestamp > 1e10:  # milliseconds
                    dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                else:  # seconds
                    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            elif isinstance(timestamp, str):
                # String timestamp
                if 'T' in timestamp:
                    # ISO format
                    dt = dateutil.parser.isoparse(timestamp)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                else:
                    # Try other formats
                    for fmt in ['%Y%m%d-%H%M%S', '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S']:
                        try:
                            dt = datetime.strptime(timestamp, fmt)
                            return timezone.make_aware(dt)
                        except ValueError:
                            continue
                    return None
            elif isinstance(timestamp, datetime):
                # Already datetime
                if timestamp.tzinfo is None:
                    return timezone.make_aware(timestamp)
                return timestamp
            return None
        except Exception as e:
            logger.error(f"Error parsing timestamp {timestamp}: {e}")
            return None

    def calculate_connection_status(self, last_update_time):
        """Расчет статуса связи на основе времени последнего обновления"""
        if not last_update_time:
            return 'long_offline'

        now = timezone.now()
        time_diff = now - last_update_time

        if time_diff <= timedelta(hours=1):
            return 'online'
        elif time_diff <= timedelta(hours=24):
            return 'no_connection'
        else:
            return 'long_offline'

    def format_time_display(self, last_update_time):
        """Форматирование времени для отображения"""
        if not last_update_time:
            return '—'

        now = timezone.now()
        time_diff = now - last_update_time

        if time_diff < timedelta(minutes=1):
            return 'только что'
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            return f'{minutes} мин назад'
        elif time_diff < timedelta(hours=24):
            hours = int(time_diff.total_seconds() / 3600)
            return f'{hours} ч назад'
        else:
            days = time_diff.days
            return f'{days} дн назад'

    def extract_license_plate_from_properties(self, properties):
        """Извлечение госномера из свойств ТС"""
        try:
            if not properties or not isinstance(properties, list):
                return None

            for prop in properties:
                if prop.get('Name') == 'VehicleRegNumber':
                    value = prop.get('Value')
                    if value and isinstance(value, str) and value.strip():
                        license_plate = value.strip()
                        logger.info(f"✅ Found license plate in properties: {license_plate}")
                        return license_plate

            return None

        except Exception as e:
            logger.error(f"❌ Error extracting license plate from properties: {e}")
            return None

    def parse_vehicle_data(self, vehicle_info, online_data):
        """Парсинг данных по ТС"""
        try:
            vehicle_id = vehicle_info.get('ID')
            vehicle_name = vehicle_info.get('Name', 'Unknown')

            # Извлекаем госномер из свойств
            properties = vehicle_info.get('Properties', [])
            license_plate = self.extract_license_plate_from_properties(properties)

            # Если не нашли в свойствах, используем fallback
            if not license_plate:
                license_plate = self.extract_license_plate_fallback(vehicle_name)

            # Получаем онлайн данные для этого ТС
            vehicle_online_data = online_data.get(str(vehicle_id), {})

            # Парсим онлайн данные
            speed = vehicle_online_data.get('Speed', 0)
            if speed:
                try:
                    speed = float(speed)
                except (ValueError, TypeError):
                    speed = 0

            # Время последнего обновления
            dt_timestamp = vehicle_online_data.get('DT')
            last_update_time = self.parse_timestamp(dt_timestamp)

            # Статус связи
            connection_status = self.calculate_connection_status(last_update_time)
            last_update_display = self.format_time_display(last_update_time)

            # Адрес
            address = vehicle_online_data.get('Address', '')

            # Топливо из Final параметров
            final_params = vehicle_online_data.get('Final', {})
            fuel_level = final_params.get('TankMainFuelLevel')

            # Если нет TankMainFuelLevel, пробуем FL1 + FL2
            if fuel_level is None:
                fl1 = final_params.get('FL1')
                fl2 = final_params.get('FL2')
                if fl1 is not None and fl2 is not None:
                    try:
                        fuel_level = float(fl1) + float(fl2)
                    except (ValueError, TypeError):
                        fuel_level = None
                elif fl1 is not None:
                    try:
                        fuel_level = float(fl1)
                    except (ValueError, TypeError):
                        fuel_level = None

            # Координаты
            last_position = vehicle_online_data.get('LastPosition', {})
            latitude = last_position.get('Lat')
            longitude = last_position.get('Lng')

            # Форматируем топливо
            if fuel_level is not None:
                try:
                    fuel_level = round(float(fuel_level), 1)
                except (ValueError, TypeError):
                    fuel_level = None

            return {
                'id': str(vehicle_id),
                'name': vehicle_name,
                'license_plate': license_plate,
                'license_plate_number': license_plate,
                'serial': vehicle_info.get('Serial'),
                'is_online': connection_status == 'online',
                'connection_status': connection_status,
                'speed': speed,
                'latitude': latitude,
                'longitude': longitude,
                'last_update': last_update_display,
                'last_update_timestamp': dt_timestamp,
                'address': address,
                'fuel_level': fuel_level,
                'engine_hours': final_params.get('EngineHours')
            }

        except Exception as e:
            logger.error(f"❌ Error parsing vehicle data for {vehicle_info.get('Name')}: {e}")
            return None

    def extract_license_plate_fallback(self, vehicle_name):
        """Fallback метод извлечения госномера из названия"""
        try:
            if not vehicle_name:
                return "—"

            # Паттерны для извлечения госномера из названий типа "644 Freightliner"
            match = re.match(r'^(\d+)\s+', vehicle_name)
            if match:
                number = match.group(1)
                return f"{number} FR"

            numbers = re.findall(r'\d+', vehicle_name)
            if numbers:
                return f"{numbers[0]} FR"

            return vehicle_name[:8]

        except Exception as e:
            logger.error(f"❌ Error extracting license plate from {vehicle_name}: {e}")
            return vehicle_name[:8] if vehicle_name else "—"

    def get_dashboard_data(self):
        """Основной метод получения данных для дашборда"""
        if not self.login("Osipenko", "Osipenko"):
            logger.error("❌ Failed to login")
            return None

        try:
            logger.info("🔄 Starting dashboard data collection...")

            # Получаем схемы
            schemas = self.get_schemas()
            if not schemas:
                logger.error("❌ No schemas available")
                return None

            schema_id = schemas[0].get('ID')
            schema_name = schemas[0].get('Name', 'Unknown')
            logger.info(f"📋 Using schema: {schema_name} ({schema_id})")

            # Получаем список ТС
            vehicles_data = self.get_vehicles(schema_id)
            if not vehicles_data or 'Items' not in vehicles_data:
                logger.error("❌ No vehicles data received")
                return None

            # Получаем онлайн данные
            online_data = self.get_online_info_all(schema_id)
            logger.info(f"📊 Got online data for {len(online_data)} vehicles")

            # Обрабатываем данные
            vehicles = []
            online_count = 0
            no_connection_count = 0
            long_offline_count = 0

            for vehicle_info in vehicles_data['Items']:
                parsed_data = self.parse_vehicle_data(vehicle_info, online_data)
                if parsed_data:
                    vehicles.append(parsed_data)

                    # Считаем статистику
                    if parsed_data['connection_status'] == 'online':
                        online_count += 1
                    elif parsed_data['connection_status'] == 'no_connection':
                        no_connection_count += 1
                    else:
                        long_offline_count += 1

            total_vehicles = len(vehicles)

            logger.info(
                f"📈 Dashboard stats: {online_count} online, {no_connection_count} no connection, {long_offline_count} long offline")

            return {
                'total_vehicles': total_vehicles,
                'online_vehicles': online_count,
                'no_connection_vehicles': no_connection_count,
                'long_offline_vehicles': long_offline_count,
                'vehicles': vehicles,
                'schema_name': schema_name,
                'last_update': timezone.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {e}")
            return None

    def get_vehicle_details(self, vehicle_id):
        """Получение детальной информации по ТС"""
        if not self.login("Osipenko", "Osipenko"):
            return None

        try:
            schemas = self.get_schemas()
            if not schemas:
                return None

            schema_id = schemas[0].get('ID')

            # Получаем список ТС
            vehicles_data = self.get_vehicles(schema_id)
            vehicle_info = None

            for vehicle in vehicles_data.get('Items', []):
                if str(vehicle.get('ID')) == vehicle_id:
                    vehicle_info = vehicle
                    break

            if not vehicle_info:
                return None

            # Получаем онлайн данные
            online_data = self.get_online_info_all(schema_id)

            # Парсим данные
            parsed_data = self.parse_vehicle_data(vehicle_info, online_data)

            return parsed_data

        except Exception as e:
            logger.error(f"❌ Error getting vehicle details: {e}")
            return None