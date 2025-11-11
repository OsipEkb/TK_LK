# vehicles/services.py
import requests
import logging
from django.conf import settings

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
                'finalParams': 'Speed,FuelLevel,EngineHours',
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

    def get_dashboard_summary(self, schema_id):
        """Получение сводных данных для дашборда - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not self.token:
            return None

        try:
            # Получаем все ТС в схеме
            vehicles_data = self.get_vehicles(schema_id)

            if not vehicles_data or 'Items' not in vehicles_data:
                return None

            # Получаем онлайн информацию для всех ТС
            online_info = self.get_online_info_all(schema_id)

            total_vehicles = len(vehicles_data['Items'])
            online_vehicles = 0
            vehicles_with_data = []

            # Считаем онлайн ТС и формируем данные
            for vehicle in vehicles_data['Items']:
                vehicle_id = str(vehicle.get('ID'))
                vehicle_info = online_info.get(vehicle_id, {})

                # УПРОЩЕННАЯ ЛОГИКА ОПРЕДЕЛЕНИЯ ОНЛАЙН СТАТУСА
                # Если есть какие-либо данные в online_info - считаем онлайн
                is_online = bool(vehicle_info)

                if is_online:
                    online_vehicles += 1

                # Извлекаем данные
                speed = vehicle_info.get('speed', 0)
                last_position = vehicle_info.get('lastPosition', {})
                latitude = last_position.get('lat')
                longitude = last_position.get('lng')
                last_update = vehicle_info.get('dt') or vehicle_info.get('lastData')
                address = vehicle_info.get('address', '')

                # Получаем финальные параметры если есть
                final_params = vehicle_info.get('final', {})
                fuel_level = final_params.get('FuelLevel')
                engine_hours = final_params.get('EngineHours')

                vehicles_with_data.append({
                    'id': vehicle_id,
                    'name': vehicle.get('Name', 'Unknown'),
                    'license_plate': self.extract_license_plate(vehicle),
                    'is_online': is_online,
                    'speed': speed,
                    'latitude': latitude,
                    'longitude': longitude,
                    'last_update': last_update,
                    'address': address,
                    'fuel_level': fuel_level,
                    'engine_hours': engine_hours
                })

            summary = {
                'total_vehicles': total_vehicles,
                'online_vehicles': online_vehicles,
                'offline_vehicles': total_vehicles - online_vehicles,
                'vehicles': vehicles_with_data,
                'last_update': self.get_current_timestamp()
            }

            logger.info(f"📈 Dashboard summary: {online_vehicles}/{total_vehicles} online")
            return summary

        except Exception as e:
            logger.error(f"❌ Error getting dashboard summary: {e}")
            return None

    def get_vehicle_monitoring_data(self, schema_id, device_id, period_minutes=5):
        """Получение данных мониторинга для конкретного ТС за период"""
        if not self.token:
            logger.error("No token available for monitoring data")
            return None

        try:
            # Получаем онлайн информацию о ТС
            online_info = self.get_online_info(schema_id, [device_id])
            logger.info(f"📊 Online info for {device_id}: {online_info}")

            if online_info:
                # Ищем данные устройства в ответе
                vehicle_data = None
                if 'Items' in online_info and online_info['Items']:
                    vehicle_data = online_info['Items'][0]
                elif device_id in online_info:
                    vehicle_data = online_info[device_id]

                if vehicle_data:
                    # Формируем структуру данных для дашборда
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

    def debug_online_data(self, schema_id):
        """Метод для отладки структуры онлайн данных"""
        if not self.token:
            return None

        try:
            online_info = self.get_online_info_all(schema_id)
            print("🔍 ДЕБАГ онлайн данных:")
            print(f"Количество записей: {len(online_info)}")

            for vehicle_id, data in list(online_info.items())[:2]:  # Покажем первые 2
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

    def extract_license_plate(self, vehicle_data):
        """Извлечение госномера из свойств ТС"""
        try:
            properties = vehicle_data.get('properties', [])
            for prop in properties:
                if prop.get('name') in ['LicensePlate', 'Госномер', 'Номер']:
                    return prop.get('value', '')
            return vehicle_data.get('Name', '')
        except:
            return vehicle_data.get('Name', '')

    def get_current_timestamp(self):
        """Текущее время для меток обновления"""
        from django.utils import timezone
        return timezone.now().isoformat()

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
        """Получение табличных данных для графиков - ОСНОВНОЙ МЕТОД ДЛЯ ГРАФИКОВ"""
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/ServiceJSON/GetTripTables"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id,
                'SD': start_date,  # Формат: yyyyMMdd или yyyyMMdd-HHmm
                'ED': end_date,  # Формат: yyyyMMdd или yyyyMMdd-HHmm
                'onlineParams': ','.join(parameters),
                'tripSplitterIndex': -1  # Не разбивать на рейсы
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