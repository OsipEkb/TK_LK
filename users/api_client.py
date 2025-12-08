# users/api_client.py
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AutoGraphAPIClient:
    """Клиент для работы с AutoGRAPH API"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Django-Monitoring-App/1.0'
        })

    def login(self, username: str, password: str, utc_offset: int = 300) -> Optional[str]:
        """
        Аутентификация в AutoGRAPH API
        Возвращает токен сессии или None
        """
        url = f"{self.BASE_URL}/Login"
        params = {
            'UserName': username,
            'Password': password,
            'UTCOffset': utc_offset
        }

        try:
            logger.info(f"🔐 AutoGRAPH login attempt for user: {username}")

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200 and response.text.strip():
                token = response.text.strip()
                logger.info(f"✅ AutoGRAPH login successful, token received (length: {len(token)})")
                return token
            elif response.status_code == 401:
                logger.error(f"❌ AutoGRAPH login failed: 401 Unauthorized")
                return None
            else:
                logger.error(f"❌ AutoGRAPH login failed: Status {response.status_code}")
                logger.debug(f"Response text: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            logger.error("⌛ AutoGRAPH login timeout")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("🔌 AutoGRAPH connection error")
            return None
        except Exception as e:
            logger.error(f"💥 AutoGRAPH login exception: {e}")
            return None

    def make_request(self, endpoint: str, params: Dict[str, Any] = None, token: str = None) -> Optional[Dict]:
        """Выполнить запрос к AutoGRAPH API"""
        url = f"{self.BASE_URL}/{endpoint}"

        if params is None:
            params = {}

        if token:
            params['session'] = token

        try:
            logger.debug(f"🌐 AutoGRAPH API request: {endpoint}")
            logger.debug(f"Params: {params}")

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    logger.error(f"❌ JSON decode error for {endpoint}: {e}")
                    logger.debug(f"Response text: {response.text[:500]}")
                    return None
            elif response.status_code == 401:
                logger.error(f"🔑 AutoGRAPH API {endpoint}: 401 Unauthorized - token invalid")
                return None
            else:
                logger.error(f"⚠️ AutoGRAPH API {endpoint} error: {response.status_code}")
                logger.debug(f"Response: {response.text[:200]}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"🔌 AutoGRAPH API {endpoint} connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"💥 AutoGRAPH API {endpoint} exception: {e}")
            return None

    def enum_schemas(self, token: str) -> Optional[list]:
        """Получить список схем"""
        return self.make_request("EnumSchemas", token=token)

    def enum_devices(self, token: str, schema_id: str) -> Optional[Dict]:
        """Получить список устройств"""
        params = {'schemaID': schema_id}
        return self.make_request("EnumDevices", params=params, token=token)

    def get_online_info(self, token: str, schema_id: str, device_ids: str) -> Optional[Dict]:
        """Получить онлайн информацию об устройствах"""
        params = {
            'schemaID': schema_id,
            'IDs': device_ids
        }
        return self.make_request("GetOnlineInfo", params=params, token=token)

    def get_track(self, token: str, schema_id: str, device_id: str, start_date: str, end_date: str) -> Optional[Dict]:
        """Получить трек устройства"""
        params = {
            'schemaID': schema_id,
            'IDs': device_id,
            'SD': start_date,
            'ED': end_date,
            'tripSplitterIndex': -1
        }
        return self.make_request("GetTrack", params=params, token=token)