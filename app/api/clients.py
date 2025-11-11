import requests
import logging
from django.conf import settings
from datetime import datetime, timedelta
import json
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class AutoGraphAPIClient:
    """Клиент для работы с AutoGRAPH API"""

    def __init__(self, username=None, password=None, token=None):
        self.base_url = "https://service.autograph-online.com"
        self.session = requests.Session()
        self.token = token
        self.username = username
        self.password = password

        # Отключаем проверку SSL для тестирования
        self.session.verify = False

logger = logging.getLogger(__name__)


class AutoGraphAPIClient:
    """Клиент для работы с AutoGRAPH API"""

    def __init__(self, username=None, password=None, token=None):
        self.base_url = "https://service.autograph-online.com"
        self.session = requests.Session()
        self.token = token
        self.username = username
        self.password = password

    def login(self, username=None, password=None):
        """Аутентификация в AutoGRAPH"""
        try:
            # Используем переданные учетные данные или сохраненные
            auth_username = username or self.username
            auth_password = password or self.password

            if not auth_username or not auth_password:
                logger.error("No credentials provided")
                return False

            url = f"{self.base_url}/ServiceJSON/Login"
            params = {
                'UserName': auth_username,
                'Password': auth_password,
                'UTCOffset': 180  # Moscow UTC+3
            }

            logger.info(f"🔄 AutoGRAPH login: {auth_username}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                self.token = response.text.strip('"')
                if self.token and self.token != '""':
                    logger.info(f"✅ AutoGRAPH login successful")
                    return True
            return False

        except Exception as e:
            logger.error(f"❌ AutoGRAPH login error: {e}")
            return False

    def get_schemas(self):
        if not self.token:
            if not self.login():
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