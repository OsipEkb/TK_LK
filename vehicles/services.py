# vehicles/services.py
import requests
import logging
import re
from django.conf import settings
from datetime import datetime

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

            print(f"🌐 SERVICE API CALL URL: {url}")
            print(f"🔑 SERVICE CREDENTIALS: UserName={username}, Password={'*' * len(password)}")
            print(f"⚙️ SERVICE PARAMS: {params}")

            logger.info(f"🔄 Logging in to AutoGRAPH: {username}")
            response = self.session.get(url, params=params, timeout=30)

            print(f"📡 SERVICE RESPONSE STATUS: {response.status_code}")
            print(f"📡 SERVICE RESPONSE TEXT: {response.text}")
            print(f"📡 SERVICE RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code == 200:
                self.token = response.text.strip('"')
                if self.token and self.token != '""':
                    print(f"✅ SERVICE Login successful, token length: {len(self.token)}")
                    print(f"✅ SERVICE Token preview: {self.token[:50]}...")
                    logger.info(f"✅ Login successful, token: {self.token[:20]}...")
                    return True
                else:
                    print("❌ SERVICE Invalid credentials - empty token")
                    logger.error("❌ Invalid credentials - empty token")
                    return False
            elif response.status_code == 401:
                print("❌ SERVICE Authentication failed - 401 Unauthorized")
                logger.error("❌ Authentication failed - 401 Unauthorized")
                return False
            else:
                print(f"❌ SERVICE Login failed with status: {response.status_code}")
                logger.error(f"❌ Login failed with status: {response.status_code}")
                return False

        except Exception as e:
            print(f"💥 SERVICE Connection error: {e}")
            import traceback
            traceback.print_exc()
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

    def get_vehicle_properties(self, schema_id, device_ids):
        """Получение свойств ТС - КЛЮЧЕВОЙ МЕТОД ДЛЯ ГОСНОМЕРОВ"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetProperties"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids)
            }

            logger.info(f"🔄 Getting properties for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got properties data for {len(device_ids)} devices")

                # Логируем структуру данных для отладки
                if data:
                    sample_key = next(iter(data.keys())) if isinstance(data, dict) else None
                    logger.info(f"🔍 Properties data structure: {type(data)}, sample key: {sample_key}")
                    if sample_key and isinstance(data[sample_key], dict):
                        logger.info(f"🔍 Sample properties keys: {list(data[sample_key].keys())}")

                return data
            else:
                logger.error(f"❌ Failed to get properties: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting properties: {e}")
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
                'finalParams': 'Speed,FuelLevel,EngineHours,Latitude,Longitude',
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

    def get_online_info(self, schema_id, device_ids):
        """Получение онлайн информации по устройствам"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids)
            }

            logger.info(f"🔄 Getting online info for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got online info for devices")
                return data
            else:
                logger.error(f"❌ Failed to get online info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting online info: {e}")
            return {}

    def parse_online_data(self, online_info, vehicle_id):
        """Парсинг онлайн данных для конкретного ТС - ДЕТАЛЬНАЯ ОТЛАДКА"""
        try:
            if not online_info:
                print(f"❌ No online info for {vehicle_id}")
                return None

            vehicle_info = online_info.get(vehicle_id, {})
            if not vehicle_info:
                print(f"❌ Vehicle {vehicle_id} not found in online info")
                return None

            print(f"🔍 Parsing online data for {vehicle_id}:")
            print(f"   Available keys: {list(vehicle_info.keys())}")

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

            # Извлекаем финальные параметры - ДЕТАЛЬНАЯ ОТЛАДКА
            final_params = vehicle_info.get('Final', {})
            print(f"   Final params: {final_params}")
            print(f"   Final params keys: {list(final_params.keys())}")

            # УЛУЧШЕННЫЙ ПОИСК ТОПЛИВА
            fuel_level = None

            # Вариант 1: TankMainFuelLevel (основной бак)
            if 'TankMainFuelLevel' in final_params:
                fuel_level = final_params['TankMainFuelLevel']
                print(f"   ✅ Found TankMainFuelLevel: {fuel_level}")

            # Вариант 2: FL1, FL2 (датчики уровня топлива)
            if fuel_level is None:
                fl1 = final_params.get('FL1')
                fl2 = final_params.get('FL2')
                print(f"   FL1: {fl1}, FL2: {fl2}")
                if fl1 is not None and fl2 is not None:
                    fuel_level = fl1 + fl2  # Суммируем оба бака
                    print(f"   ✅ Sum FL1+FL2: {fuel_level}")
                elif fl1 is not None:
                    fuel_level = fl1
                    print(f"   ✅ Using FL1: {fuel_level}")
                elif fl2 is not None:
                    fuel_level = fl2
                    print(f"   ✅ Using FL2: {fuel_level}")

            # Вариант 3: FuelLevel (общий уровень)
            if fuel_level is None:
                fuel_level = final_params.get('FuelLevel')
                if fuel_level is not None:
                    print(f"   ✅ Found FuelLevel: {fuel_level}")

            # Вариант 4: Ищем в других полях
            if fuel_level is None:
                for key, value in final_params.items():
                    if 'fuel' in key.lower() or 'tank' in key.lower():
                        if isinstance(value, (int, float)) and value > 0:
                            fuel_level = value
                            print(f"   ✅ Found in {key}: {fuel_level}")
                            break

            engine_hours = final_params.get('EngineHours')

            # Парсим числовые значения
            if fuel_level:
                try:
                    fuel_level = float(fuel_level)
                    # Округляем до 1 знака после запятой
                    fuel_level = round(fuel_level, 1)
                    print(f"   ✅ Final fuel level: {fuel_level}")
                except (ValueError, TypeError):
                    fuel_level = None
                    print(f"   ❌ Error parsing fuel level")
            else:
                print(f"   ❌ No fuel level found")

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

            print(f"✅ Final parsed data for {vehicle_id}: fuel={fuel_level}")
            return result

        except Exception as e:
            logger.error(f"❌ Error parsing online data for {vehicle_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _extract_license_plate_from_name(self, name):
        """Извлечение госномера из имени ТС"""
        try:
            if not name:
                return None

            # Паттерны для российских госномеров
            patterns = [
                r'(\d{3}\s*[A-ZА-Я]{2}\s*\d{2,3})',  # 123 АБ 45
                r'([A-ZА-Я]{1,2}\s*\d{3,4}\s*[A-ZА-Я]{1,2})',  # А 1234 БС
                r'(\d{2,3}\s*[A-ZА-Я]{1,2}\s*\d{2,3})',  # 12 АБ 345
                r'([A-ZА-Я]{2}\s*\d{3})',  # АБ 123
                r'(\d{3}\s*[A-ZА-Я]{2})',  # 123 АБ
            ]

            for pattern in patterns:
                match = re.search(pattern, name.upper())
                if match:
                    license_plate = match.group(1).strip()
                    # Убедимся, что это действительно похоже на госномер
                    if len(license_plate) >= 5:  # Минимальная длина госномера
                        return license_plate

            return None

        except Exception as e:
            logger.error(f"❌ Error extracting license plate from name: {e}")
            return None

    def _extract_from_properties_data(self, properties_data, vehicle_id):
        """Извлечение госномера из данных свойств"""
        try:
            if not properties_data:
                return None

            # Разные возможные структуры данных свойств
            license_plate_keys = ['LicensePlate', 'Госномер', 'Номер', 'Plate', 'StateNumber', 'Гос.номер']

            # Вариант 1: свойства по vehicle_id
            if vehicle_id in properties_data:
                vehicle_props = properties_data[vehicle_id]
                if isinstance(vehicle_props, dict):
                    for key, value in vehicle_props.items():
                        for license_key in license_plate_keys:
                            if license_key.lower() in key.lower() and value:
                                logger.info(f"✅ Found license plate in properties data: {key} = {value}")
                                return str(value).strip()

            # Вариант 2: свойства в Items
            if 'Items' in properties_data:
                for item in properties_data['Items']:
                    if str(item.get('ID')) == vehicle_id:
                        properties = item.get('Properties', [])
                        for prop in properties:
                            prop_name = prop.get('Name') or prop.get('name', '')
                            prop_value = prop.get('Value') or prop.get('value', '')
                            for license_key in license_plate_keys:
                                if license_key.lower() in prop_name.lower() and prop_value:
                                    logger.info(
                                        f"✅ Found license plate in properties Items: {prop_name} = {prop_value}")
                                    return str(prop_value).strip()

            return None

        except Exception as e:
            logger.error(f"❌ Error extracting from properties data: {e}")
            return None

    def extract_license_plate_enhanced(self, vehicle_data, properties_data=None):
        """УЛУЧШЕННОЕ извлечение госномера - используем GetPropertiesTable"""
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

            # Получаем свойства для всех ТС (GetPropertiesTable)
            device_ids = [str(vehicle.get('ID')) for vehicle in vehicles_data['Items']]
            logger.info(f"🔄 Getting properties for {len(device_ids)} devices")

            properties_data = self.get_vehicle_properties_table(schema_id, device_ids)
            logger.info(f"📊 Got properties data: {len(properties_data)} devices with properties")

            # ВАЖНО: Используем GetOnlineInfo_with_fuel для получения данных с топливом
            print("🔄 Getting online info WITH FUEL DATA...")
            online_info = self.get_online_info_with_fuel(schema_id, device_ids)

            if not online_info:
                print("❌ GetOnlineInfo_with_fuel returned no data, trying regular GetOnlineInfo...")
                online_info = self.get_online_info(schema_id, device_ids)

            if not online_info:
                print("❌ All online info methods failed, using GetOnlineInfoAll as fallback...")
                online_info = self.get_online_info_all(schema_id)

            logger.info(f"📊 Final online info: {len(online_info)} devices online")

            total_vehicles = len(vehicles_data['Items'])
            online_vehicles = 0
            vehicles_with_data = []

            for vehicle in vehicles_data['Items']:
                vehicle_id = str(vehicle.get('ID'))
                vehicle_name = vehicle.get('Name', 'Unknown')

                # Извлекаем госномер УЛУЧШЕННЫМ методом
                license_plate = self.extract_license_plate_enhanced(vehicle, properties_data)

                # Парсим онлайн данные (теперь с топливом!)
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
            import traceback
            logger.error(traceback.format_exc())
            return None

    def get_dashboard_summary(self, schema_id):
        """Получение сводных данных для дашборда - используем улучшенную версию"""
        return self.get_enhanced_dashboard_summary(schema_id)

    def get_vehicle_monitoring_data(self, schema_id, device_id, period_minutes=5):
        """Получение данных мониторинга для конкретного ТС за период"""
        if not self.token:
            logger.error("No token available for monitoring data")
            return None

        try:
            online_info = self.get_online_info(schema_id, [device_id])
            logger.info(f"📊 Online info for {device_id}: {online_info}")

            if online_info:
                vehicle_data = None
                if 'Items' in online_info and online_info['Items']:
                    vehicle_data = online_info['Items'][0]
                elif device_id in online_info:
                    vehicle_data = online_info[device_id]

                if vehicle_data:
                    monitoring_data = {
                        'vehicle_id': device_id,
                        'vehicle_name': vehicle_data.get('Name', 'Unknown'),
                        'latitude': vehicle_data.get('lastPosition', {}).get('lat'),
                        'longitude': vehicle_data.get('lastPosition', {}).get('lng'),
                        'speed': vehicle_data.get('speed', 0),
                        'timestamp': vehicle_data.get('dt') or vehicle_data.get('lastData'),
                        'fuel_level': vehicle_data.get('final', {}).get('FuelLevel'),
                        'engine_hours': vehicle_data.get('final', {}).get('EngineHours'),
                        'is_online': bool(vehicle_data),
                        'last_update': vehicle_data.get('dt') or vehicle_data.get('lastData'),
                        'address': vehicle_data.get('address', '')
                    }

                    logger.info(f"✅ Monitoring data for {device_id}: speed={monitoring_data['speed']}")
                    return monitoring_data

            logger.warning(f"⚠️ No online data for device {device_id}")
            return None

        except Exception as e:
            logger.error(f"❌ Error getting monitoring data for {device_id}: {e}")
            return None

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

            # Получаем свойства
            properties = self.get_vehicle_properties(schema_id, [device_id])

            # Получаем онлайн данные
            online_data = self.get_online_info(schema_id, [device_id])

            # Извлекаем госномер
            license_plate = self.extract_license_plate_enhanced(vehicle_info, properties)

            # Формируем ответ
            detailed_info = {
                'basic_info': vehicle_info,
                'properties': properties,
                'online_data': online_data,
                'license_plate': license_plate
            }

            return detailed_info

        except Exception as e:
            logger.error(f"❌ Error getting detailed vehicle info: {e}")
            return None

    def get_current_timestamp(self):
        """Текущее время для меток обновления"""
        from django.utils import timezone
        return timezone.now().isoformat()

    def debug_online_data(self, schema_id):
        """Метод для отладки структуры онлайн данных"""
        if not self.token:
            return None

        try:
            online_info = self.get_online_info_all(schema_id)
            print("🔍 ДЕБАГ онлайн данных:")
            print(f"Количество записей: {len(online_info)}")

            for vehicle_id, data in list(online_info.items())[:2]:
                print(f"\nТС ID: {vehicle_id}")
                print(f"Данные: {data}")
                if data:
                    print(f"Ключи: {list(data.keys())}")
                    print(f"lastPosition: {data.get('lastPosition')}")
                    print(f"speed: {data.get('speed')}")
                    print(f"dt: {data.get('dt')}")
                    print(f"final: {data.get('final')}")
                else:
                    print("Данные пустые")

            return online_info
        except Exception as e:
            print(f"Ошибка отладки: {e}")
            return None

    # Остальные методы остаются без изменений
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

    def get_vehicle_parameters(self, schema_id, device_id):
        """Получение доступных параметров для ТС (топливо, датчики и т.д.)"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumParameters"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id
            }

            logger.info(f"🔄 Getting parameters for device: {device_id}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got parameters for device {device_id}")
                return data
            else:
                logger.error(f"❌ Failed to get parameters: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting parameters: {e}")
            return {}

    def get_trip_tables(self, schema_id, device_id, start_date, end_date, parameters):
        """Получение табличных данных для графиков"""
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/ServiceJSON/GetTripTables"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id,
                'SD': start_date,
                'ED': end_date,
                'onlineParams': ','.join(parameters),
                'tripSplitterIndex': -1
            }

            logger.info(f"🔄 Getting trip tables for {device_id} with params: {parameters}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got trip tables data for {device_id}")
                return data
            else:
                logger.error(f"❌ Failed to get trip tables: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting trip tables: {e}")
            return None

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

    def format_date_for_api(self, date_string, include_time=False):
        """Форматирование даты для API AutoGRAPH"""
        from datetime import datetime

        try:
            if include_time:
                # yyyyMMdd-HHmm
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return dt.strftime('%Y%m%d-%H%M')
            else:
                # yyyyMMdd
                dt = datetime.fromisoformat(date_string.split('T')[0])
                return dt.strftime('%Y%m%d')
        except Exception as e:
            logger.error(f"❌ Error formatting date: {e}")
            return date_string

    def get_devices_info(self, schema_id, device_ids):
        """Получение информации об устройствах в схеме"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetDevicesInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids)
            }

            logger.info(f"🔄 Getting devices info for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got devices info for {len(device_ids)} devices")
                print(f"📊 GetDevicesInfo raw data: {data}")
                return data
            else:
                logger.error(f"❌ Failed to get devices info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting devices info: {e}")
            return {}

    def get_property_table(self, schema_id, device_ids, property_name):
        """Получение значения одного свойства у ТС в виде таблицы"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetPropertyTable"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids),
                'property': property_name
            }

            logger.info(f"🔄 Getting property '{property_name}' for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got property '{property_name}' for devices")
                return data
            else:
                logger.error(f"❌ Failed to get property '{property_name}': {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting property '{property_name}': {e}")
            return {}

    def debug_properties_structure(self, schema_id, vehicle_ids):
        """Детальный анализ структуры свойств"""
        try:
            print("🔍 DETAILED PROPERTIES DEBUG")

            # Получаем свойства
            properties_data = self.get_vehicle_properties(schema_id, vehicle_ids)

            results = {}

            for vehicle_id in vehicle_ids:
                print(f"\n=== Analyzing vehicle {vehicle_id} ===")

                if vehicle_id in properties_data:
                    vehicle_data = properties_data[vehicle_id]
                    print(f"Vehicle data keys: {list(vehicle_data.keys())}")

                    # Анализируем Properties
                    if 'Properties' in vehicle_data:
                        properties_list = vehicle_data['Properties']
                        print(f"Number of properties: {len(properties_list)}")

                        license_plate_found = False
                        for prop in properties_list:
                            prop_name = prop.get('Name', '')
                            prop_value = prop.get('Value', '')
                            print(f"  Property: '{prop_name}' = '{prop_value}'")

                            # Ищем госномер
                            if any(key in prop_name for key in ['LicensePlate', 'Госномер', 'Номер']):
                                print(f"  ✅ FOUND LICENSE PLATE: {prop_name} = {prop_value}")
                                license_plate_found = True

                        if not license_plate_found:
                            print("  ❌ No license plate found in properties")

                    # Анализируем PropertyTypes
                    if 'PropertyTypes' in vehicle_data:
                        print(f"PropertyTypes: {vehicle_data['PropertyTypes']}")

                    # Анализируем PropertyComments
                    if 'PropertyComments' in vehicle_data:
                        print(f"PropertyComments: {vehicle_data['PropertyComments']}")

                    results[vehicle_id] = {
                        'properties': vehicle_data.get('Properties', []),
                        'property_types': vehicle_data.get('PropertyTypes', []),
                        'property_comments': vehicle_data.get('PropertyComments', [])
                    }
                else:
                    print(f"❌ Vehicle {vehicle_id} not found in properties data")
                    results[vehicle_id] = None

            return results

        except Exception as e:
            print(f"❌ Error in debug_properties_structure: {e}")
            import traceback
            traceback.print_exc()
            return None

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
                print(f"📊 GetPropertiesTable raw data: {data}")
                return data
            else:
                logger.error(f"❌ Failed to get properties table: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting properties table: {e}")
            return {}

        def get_enhanced_dashboard_summary(self, schema_id):
            """УЛУЧШЕННАЯ версия получения данных для дашборда со свойствами"""
            if not self.token:
                logger.error("❌ No token available")
                return None

            try:
                print("🚀 STARTING ENHANCED DASHBOARD SUMMARY")
                logger.info("🔄 Starting enhanced dashboard summary...")

                # Получаем все ТС
                vehicles_data = self.get_vehicles(schema_id)
                print(f"📊 Got {len(vehicles_data.get('Items', []))} vehicles")

                if not vehicles_data or 'Items' not in vehicles_data:
                    logger.error("❌ No vehicles data received")
                    return None

                # Получаем свойства для всех ТС (GetPropertiesTable)
                device_ids = [str(vehicle.get('ID')) for vehicle in vehicles_data['Items']]
                print(f"🔄 Getting properties for {len(device_ids)} devices")

                properties_data = self.get_vehicle_properties_table(schema_id, device_ids)
                print(f"📊 Got properties for {len(properties_data)} devices")

                # ВАЖНО: Используем GetOnlineInfo_with_fuel для получения данных с топливом
                print("🔄 Getting online info WITH FUEL DATA...")
                online_info = self.get_online_info_with_fuel(schema_id, device_ids)

                if online_info:
                    print(f"✅ Got online info with fuel for {len(online_info)} devices")
                    # Проверим первый автомобиль
                    first_vehicle_id = list(online_info.keys())[0] if online_info else None
                    if first_vehicle_id:
                        first_vehicle = online_info[first_vehicle_id]
                        print(f"🔍 First vehicle data:")
                        print(f"   Final keys: {list(first_vehicle.get('Final', {}).keys())}")
                        print(f"   Fuel data: {first_vehicle.get('Final', {})}")
                else:
                    print("❌ GetOnlineInfo_with_fuel returned no data, trying regular GetOnlineInfo...")
                    online_info = self.get_online_info(schema_id, device_ids)

                if not online_info:
                    print("❌ All online info methods failed, using GetOnlineInfoAll as fallback...")
                    online_info = self.get_online_info_all(schema_id)

                print(f"📊 Final online info: {len(online_info)} devices")

                total_vehicles = len(vehicles_data['Items'])
                online_vehicles = 0
                vehicles_with_data = []

                for vehicle in vehicles_data['Items']:
                    vehicle_id = str(vehicle.get('ID'))
                    vehicle_name = vehicle.get('Name', 'Unknown')

                    # Извлекаем госномер УЛУЧШЕННЫМ методом
                    license_plate = self.extract_license_plate_enhanced(vehicle, properties_data)

                    # Парсим онлайн данные (теперь с топливом из онлайн данных!)
                    print(f"🔄 Parsing data for {vehicle_name}...")
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
                        # Топливо из онлайн данных!
                        'engine_hours': online_data_parsed.get('engine_hours') if online_data_parsed else None
                    }

                    vehicles_with_data.append(vehicle_data)

                    fuel_display = vehicle_data['fuel_level'] if vehicle_data[
                                                                     'fuel_level'] is not None else "нет данных"
                    print(f"✅ {vehicle_name}: Fuel={fuel_display}, Online={is_online}")

                summary = {
                    'total_vehicles': total_vehicles,
                    'online_vehicles': online_vehicles,
                    'offline_vehicles': total_vehicles - online_vehicles,
                    'vehicles': vehicles_with_data,
                    'last_update': self.get_current_timestamp()
                }

                # Посчитаем ТС с топливом
                vehicles_with_fuel = [v for v in vehicles_with_data if v.get('fuel_level') is not None]
                print(f"🎯 FINAL RESULT: {len(vehicles_with_fuel)}/{total_vehicles} vehicles with fuel data")

                return summary

            except Exception as e:
                logger.error(f"❌ Error getting enhanced dashboard summary: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None

    def get_fuel_level_from_properties(self, vehicle_id, properties_data):
        """Получение уровня топлива из свойств ТС"""
        try:
            if not properties_data or vehicle_id not in properties_data:
                return None

            vehicle_props = properties_data[vehicle_id]
            if not isinstance(vehicle_props, list):
                return None

            fuel_data = {}

            for prop in vehicle_props:
                prop_name = prop.get('Name', '')

                # Ищем датчики уровня топлива (LLS1, LLS2 и т.д.)
                if prop_name.startswith('LLS') and prop.get('Type') == 3:  # Type 3 = тарировочная таблица
                    values = prop.get('Values', [])
                    if values and len(values) > 0:
                        table_data = values[0].get('Value', {})
                        items = table_data.get('items', [])

                        if items:
                            # Берем последнее значение из таблицы (текущий уровень)
                            last_item = items[-1] if items else {}
                            current_fuel = last_item.get('outputVal')

                            if current_fuel is not None:
                                fuel_data[prop_name] = float(current_fuel)

            # Возвращаем суммарное топливо по всем бакам
            if fuel_data:
                total_fuel = sum(fuel_data.values())
                logger.info(f"✅ Fuel levels for {vehicle_id}: {fuel_data}, total: {total_fuel}")
                return total_fuel

            return None

        except Exception as e:
            logger.error(f"❌ Error getting fuel level for {vehicle_id}: {e}")
            return None

    def get_online_info_extended(self, schema_id, device_ids):
        """Получение онлайн информации с расширенными параметрами"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids),
                'finalParams': 'Speed,FuelLevel,EngineHours,Latitude,Longitude,Address'
            }

            logger.info(f"🔄 Getting extended online info for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got extended online info for devices")
                print(f"📊 GetOnlineInfo extended raw data: {data}")
                return data
            else:
                logger.error(f"❌ Failed to get extended online info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting extended online info: {e}")
            return {}

    def get_devices_info(self, schema_id, device_ids):
        """Получение информации об устройствах в схеме"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetDevicesInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(device_ids)
            }

            logger.info(f"🔄 Getting devices info for {len(device_ids)} devices")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got devices info for {len(device_ids)} devices")
                print(f"📊 GetDevicesInfo raw data: {data}")
                return data
            else:
                logger.error(f"❌ Failed to get devices info: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error getting devices info: {e}")
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