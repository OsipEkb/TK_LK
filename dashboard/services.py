# dashboard/services.py
import requests
import logging
import re
from django.conf import settings
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


class AutoGraphDashboardService:
    """Сервис для ДАШБОРДА - работа с реальными (онлайн) данными"""

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
                'finalParams': 'Speed,FuelLevel,EngineHours,Latitude,Longitude,Address',
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

    def get_online_info_with_fuel(self, schema_id, device_ids):
        """Получение онлайн информации с параметрами топлива"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids),
                'finalParams': 'TankMainFuelLevel,FL1,FL2,FuelLevel,Speed,Latitude,Longitude,Address,EngineHours'
            }

            logger.info(f"🔄 Getting online info with fuel params for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got online info with fuel params for {len(data)} devices")
                return data
            else:
                logger.error(f"❌ Failed to get online info with fuel: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting online info with fuel: {e}")
            return {}

    def parse_online_data(self, online_info, vehicle_id):
        """Парсинг онлайн данных для конкретного ТС"""
        try:
            if not online_info:
                return None

            vehicle_info = online_info.get(vehicle_id, {})
            if not vehicle_info:
                return None

            # Извлекаем скорость
            speed = vehicle_info.get('Speed', 0)
            if speed:
                try:
                    speed = float(speed)
                except (ValueError, TypeError):
                    speed = 0

            # Извлекаем координаты
            last_position = vehicle_info.get('LastPosition', {})
            latitude = last_position.get('Lat')
            longitude = last_position.get('Lng')

            # Извлекаем время последнего обновления
            last_update = vehicle_info.get('DT') or vehicle_info.get('LastData')

            # Извлекаем адрес
            address = vehicle_info.get('Address', '')

            # Извлекаем финальные параметры
            final_params = vehicle_info.get('Final', {})

            # Поиск топлива
            fuel_level = None

            # Вариант 1: TankMainFuelLevel (основной бак)
            if 'TankMainFuelLevel' in final_params:
                fuel_level = final_params['TankMainFuelLevel']

            # Вариант 2: FL1, FL2 (датчики уровня топлива)
            if fuel_level is None:
                fl1 = final_params.get('FL1')
                fl2 = final_params.get('FL2')
                if fl1 is not None and fl2 is not None:
                    fuel_level = fl1 + fl2  # Суммируем оба бака
                elif fl1 is not None:
                    fuel_level = fl1
                elif fl2 is not None:
                    fuel_level = fl2

            # Вариант 3: FuelLevel (общий уровень)
            if fuel_level is None:
                fuel_level = final_params.get('FuelLevel')

            # Вариант 4: Ищем в других полях
            if fuel_level is None:
                for key, value in final_params.items():
                    if 'fuel' in key.lower() or 'tank' in key.lower():
                        if isinstance(value, (int, float)) and value > 0:
                            fuel_level = value
                            break

            engine_hours = final_params.get('EngineHours')

            # Парсим числовые значения
            if fuel_level:
                try:
                    fuel_level = float(fuel_level)
                    fuel_level = round(fuel_level, 1)
                except (ValueError, TypeError):
                    fuel_level = None

            if engine_hours:
                try:
                    engine_hours = float(engine_hours)
                except (ValueError, TypeError):
                    engine_hours = None

            result = {
                'speed': speed,
                'latitude': latitude,
                'longitude': longitude,
                'last_update': last_update,
                'address': address,
                'fuel_level': fuel_level,
                'engine_hours': engine_hours,
                'is_online': True
            }

            return result

        except Exception as e:
            logger.error(f"❌ Error parsing online data for {vehicle_id}: {e}")
            return None

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

    def extract_license_plate_enhanced(self, vehicle_data, properties_data=None):
        """УЛУЧШЕННОЕ извлечение госномера"""
        try:
            vehicle_id = str(vehicle_data.get('ID'))
            vehicle_name = vehicle_data.get('Name', '')

            # 1. Пробуем извлечь из properties_data (GetPropertiesTable)
            if properties_data and isinstance(properties_data, dict):
                if vehicle_id in properties_data:
                    vehicle_props = properties_data[vehicle_id]
                    if isinstance(vehicle_props, list):
                        for prop in vehicle_props:
                            if prop.get('Name') == 'VehicleRegNumber':
                                values = prop.get('Values', [])
                                if values and len(values) > 0:
                                    license_plate = values[0].get('Value', '').strip()
                                    if license_plate:
                                        logger.info(f"✅ Found license plate in VehicleRegNumber: {license_plate}")
                                        return license_plate

            # 2. Пробуем извлечь из свойств vehicle_data (EnumDevices)
            properties = vehicle_data.get('properties', [])
            for prop in properties:
                if prop.get('name') in ['LicensePlate', 'Госномер', 'Номер', 'VehicleRegNumber']:
                    value = prop.get('value', '')
                    if value and value.strip():
                        license_plate = value.strip()
                        logger.info(f"✅ Found license plate in vehicle properties: {license_plate}")
                        return license_plate

            # 3. Пробуем извлечь из имени ТС (fallback)
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

    def get_enhanced_dashboard_summary(self, schema_id):
        """УЛУЧШЕННАЯ версия получения данных для дашборда со свойствами"""
        if not self.token:
            logger.error("❌ No token available")
            return None

        try:
            logger.info("🔄 Starting enhanced dashboard summary...")

            # Получаем все ТС
            vehicles_data = self.get_vehicles(schema_id)
            logger.info(f"📊 Got vehicles data: {len(vehicles_data.get('Items', []))} vehicles")

            if not vehicles_data or 'Items' not in vehicles_data:
                logger.error("❌ No vehicles data received")
                return None

            # Получаем онлайн данные
            device_ids = [str(v.get('ID')) for v in vehicles_data['Items']]
            online_info = self.get_online_info_with_fuel(schema_id, device_ids)

            if not online_info:
                online_info = self.get_online_info_all(schema_id)

            logger.info(f"📊 Final online info: {len(online_info)} devices online")

            total_vehicles = len(vehicles_data['Items'])
            online_vehicles = 0
            vehicles_with_data = []

            for vehicle in vehicles_data['Items']:
                vehicle_id = str(vehicle.get('ID'))
                vehicle_name = vehicle.get('Name', 'Unknown')

                # Извлекаем госномер
                license_plate = self.extract_license_plate_enhanced(vehicle)

                # Парсим онлайн данные
                online_data_parsed = self.parse_online_data(online_info, vehicle_id)
                is_online = online_data_parsed is not None

                if is_online:
                    online_vehicles += 1

                vehicle_data = {
                    'id': vehicle_id,
                    'name': vehicle_name,
                    'license_plate': license_plate or '',
                    'serial': vehicle.get('Serial'),
                    'is_online': is_online,
                    'speed': online_data_parsed.get('speed', 0) if online_data_parsed else 0,
                    'latitude': online_data_parsed.get('latitude') if online_data_parsed else None,
                    'longitude': online_data_parsed.get('longitude') if online_data_parsed else None,
                    'last_update': online_data_parsed.get('last_update') if online_data_parsed else None,
                    'address': online_data_parsed.get('address', '') if online_data_parsed else '',
                    'fuel_level': online_data_parsed.get('fuel_level') if online_data_parsed else None,
                    'engine_hours': online_data_parsed.get('engine_hours') if online_data_parsed else None
                }

                vehicles_with_data.append(vehicle_data)

                fuel_display = vehicle_data['fuel_level'] if vehicle_data['fuel_level'] is not None else "нет данных"
                logger.info(f"✅ Vehicle data: {vehicle_name} - Fuel: {fuel_display} - Online: {is_online}")

            summary = {
                'total_vehicles': total_vehicles,
                'online_vehicles': online_vehicles,
                'offline_vehicles': total_vehicles - online_vehicles,
                'vehicles': vehicles_with_data,
                'last_update': self.get_current_timestamp()
            }

            logger.info(f"📈 Enhanced dashboard summary: {online_vehicles}/{total_vehicles} online")
            return summary

        except Exception as e:
            logger.error(f"❌ Error getting enhanced dashboard summary: {e}")
            return None

    def get_current_timestamp(self):
        """Текущее время для меток обновления"""
        return timezone.now().isoformat()

    def get_vehicle_properties_table(self, schema_id, device_ids):
        """Получение свойств ТС в виде таблицы"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetPropertiesTable"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids)
            }

            logger.info(f"🔄 Getting properties table for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got properties table for {len(device_ids)} devices")
                return data
            else:
                logger.error(f"❌ Failed to get properties table: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting properties table: {e}")
            return {}

    def get_vehicle_detailed_info(self, schema_id, device_id):
        """Получение детальной информации по ТС включая свойства"""
        if not self.token:
            return None

        try:
            # Получаем базовую информацию
            vehicles_data = self.get_vehicles(schema_id)
            vehicle_info = None

            for vehicle in vehicles_data.get('Items', []):
                if str(vehicle.get('ID')) == device_id:
                    vehicle_info = vehicle
                    break

            if not vehicle_info:
                return None

            # Получаем онлайн данные
            online_data = self.get_online_info_with_fuel(schema_id, [device_id])

            # Извлекаем госномер
            license_plate = self.extract_license_plate_enhanced(vehicle_info)

            # Формируем ответ
            detailed_info = {
                'basic_info': vehicle_info,
                'online_data': online_data,
                'license_plate': license_plate
            }

            return detailed_info

        except Exception as e:
            logger.error(f"❌ Error getting detailed vehicle info: {e}")
            return None