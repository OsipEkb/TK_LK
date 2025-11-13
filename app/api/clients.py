import requests
import logging
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class AutoGraphAPIClient:
    """Клиент для работы с AutoGRAPH API"""

    def __init__(self):
        # ИСПРАВЛЕНО: используем тот же URL что и в AutoGraphService
        self.base_url = settings.AUTOGRAPH_API_BASE_URL  # "https://web.tk-ekat.ru"
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

            print(f"🌐 API CALL URL: {url}")
            print(f"🔑 CREDENTIALS: UserName={username}, Password={'*' * len(password)}")
            print(f"⚙️ PARAMS: {params}")

            logger.info(f"🔄 AutoGRAPH login: {username}")
            response = self.session.get(url, params=params, timeout=30)

            print(f"📡 RESPONSE STATUS: {response.status_code}")
            print(f"📡 RESPONSE TEXT: {response.text}")
            print(f"📡 RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code == 200:
                self.token = response.text.strip('"')
                if self.token and self.token != '""':
                    print(f"✅ Login successful, token length: {len(self.token)}")
                    print(f"✅ Token preview: {self.token[:50]}...")
                    return self.token  # ИСПРАВЛЕНО: возвращаем токен, а не True
                else:
                    print("❌ Invalid credentials - empty token")
                    return None  # ИСПРАВЛЕНО: возвращаем None при ошибке
            elif response.status_code == 401:
                print("❌ Authentication failed - 401 Unauthorized")
                return None  # ИСПРАВЛЕНО: возвращаем None при ошибке
            else:
                print(f"❌ Login failed with status: {response.status_code}")
                return None  # ИСПРАВЛЕНО: возвращаем None при ошибке

        except Exception as e:
            print(f"💥 Connection error: {e}")
            import traceback
            traceback.print_exc()
            return None  # ИСПРАВЛЕНО: возвращаем None при ошибке

        except Exception as e:
            print(f"💥 Connection error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_schemas(self):
        """Получение списка схем"""
        if not self.token:
            return []

        try:
            url = f"{self.base_url}/ServiceJSON/EnumSchemas"
            params = {'session': self.token}

            response = self.session.get(url, params=params, timeout=30)
            return response.json() if response.status_code == 200 else []

        except Exception as e:
            logger.error(f"❌ Error getting schemas: {e}")
            return []

    def get_vehicles(self, schema_id):
        """Получение списка ТС"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumDevices"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            response = self.session.get(url, params=params, timeout=30)
            return response.json() if response.status_code == 200 else {}

        except Exception as e:
            logger.error(f"❌ Error getting vehicles: {e}")
            return {}

    def get_trip_tables(self, schema_id, vehicle_id, start_date, end_date, parameters):
        """Получение данных для графиков - ОСНОВНОЙ МЕТОД"""
        if not self.token:
            return None

        try:
            url = f"{self.base_url}/ServiceJSON/GetTripTables"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': vehicle_id,
                'SD': start_date,  # формат: yyyyMMdd
                'ED': end_date,  # формат: yyyyMMdd
                'onlineParams': ','.join(parameters),
                'tripSplitterIndex': -1
            }

            logger.info(f"🔄 Getting trip tables for {vehicle_id}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got trip tables data for {vehicle_id}")
                return data
            return None

        except Exception as e:
            logger.error(f"❌ Error getting trip tables: {e}")
            return None

    def get_online_info(self, schema_id, vehicle_ids):
        """Получение онлайн информации по ТС"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': ','.join(vehicle_ids)
            }

            response = self.session.get(url, params=params, timeout=30)
            return response.json() if response.status_code == 200 else {}

        except Exception as e:
            logger.error(f"❌ Error getting online info: {e}")
            return {}

    def get_vehicle_parameters(self, schema_id, vehicle_id):
        """Получение доступных параметров для ТС"""
        if not self.token:
            return {}

        try:
            url = f"{self.base_url}/ServiceJSON/EnumParameters"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': vehicle_id
            }

            response = self.session.get(url, params=params, timeout=30)
            return response.json() if response.status_code == 200 else {}

        except Exception as e:
            logger.error(f"❌ Error getting parameters: {e}")
            return {}