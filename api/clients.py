import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AutoGraphAPIClient:
    """Клиент для работы с AutoGRAPH API"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
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
                logger.info(f"✅ AutoGRAPH login successful, token length: {len(token)}")
                return token
            elif response.status_code == 401:
                logger.error(f"❌ AutoGRAPH login failed: 401 Unauthorized")
                return None
            else:
                logger.error(
                    f"❌ AutoGRAPH login failed: Status {response.status_code}, Response: {response.text[:100]}")
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

    def make_request(self, endpoint: str, params: dict = None, token: str = None) -> Optional[dict]:
        """Выполнить запрос к AutoGRAPH API"""
        url = f"{self.BASE_URL}/{endpoint}"

        if params is None:
            params = {}

        if token:
            params['session'] = token

        try:
            logger.debug(f"🌐 AutoGRAPH API request: {endpoint}")

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    logger.error(f"❌ JSON decode error for {endpoint}")
                    return None
            elif response.status_code == 401:
                logger.error(f"🔑 AutoGRAPH API {endpoint}: 401 Unauthorized")
                return None
            else:
                logger.error(f"⚠️ AutoGRAPH API {endpoint} error: {response.status_code}")
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

    def enum_devices(self, token: str, schema_id: str) -> Optional[dict]:
        """Получить список устройств"""
        params = {'schemaID': schema_id}
        return self.make_request("EnumDevices", params=params, token=token)

    def get_online_info(self, token: str, schema_id: str, device_ids: str) -> Optional[dict]:
        """Получить онлайн информацию об устройствах"""
        params = {
            'schemaID': schema_id,
            'IDs': device_ids
        }
        return self.make_request("GetOnlineInfo", params=params, token=token)