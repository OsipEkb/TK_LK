# services.py - исправленная версия
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AutoGraphService:
    """Упрощенный сервис для работы с AutoGRAPH API"""

    def __init__(self):
        self.base_url = getattr(settings, 'AUTOGRAPH_API_BASE_URL', 'https://web.tk-ekat.ru')
        self.session = requests.Session()
        self.token = None

    def login(self, username: str = "Osipenko", password: str = "Osipenko") -> bool:
        """Аутентификация в AutoGRAPH с улучшенной обработкой ошибок"""
        try:
            # Проверяем кэш
            cached_token = cache.get('autograph_session_token')
            if cached_token:
                self.token = cached_token
                logger.info("✅ Используем кэшированный токен")
                return True

            url = f"{self.base_url}/ServiceJSON/Login"
            params = {
                'UserName': username,
                'Password': password,
                'UTCOffset': 180
            }

            logger.info(f"🔄 Попытка аутентификации для пользователя: {username}")
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                # Обрабатываем ответ как JSON
                try:
                    data = response.json()
                    if data.get('Success'):
                        self.token = data.get('Session')
                        # Кэшируем токен на 1 час
                        cache.set('autograph_session_token', self.token, 3600)
                        logger.info("✅ Успешная аутентификация")
                        return True
                    else:
                        logger.error(f"❌ Ошибка аутентификации: {data.get('Error', 'Unknown error')}")
                except ValueError:
                    # Если ответ не JSON, пробуем как текст
                    token_text = response.text.strip('"')
                    if token_text and token_text != '""':
                        self.token = token_text
                        cache.set('autograph_session_token', self.token, 3600)
                        logger.info("✅ Успешная аутентификация (текстовый ответ)")
                        return True
            else:
                logger.error(f"❌ HTTP ошибка при аутентификации: {response.status_code}")

            return False

        except requests.exceptions.Timeout:
            logger.error("⏰ Таймаут при аутентификации")
            return False
        except Exception as e:
            logger.error(f"❌ Исключение при аутентификации: {e}")
            return False

    def _ensure_auth(self) -> bool:
        """Проверка и обновление аутентификации"""
        if not self.token:
            return self.login()
        return True

    def get_schemas(self) -> List[Dict]:
        """Получение списка схем с улучшенной обработкой"""
        try:
            if not self._ensure_auth():
                return []

            url = f"{self.base_url}/ServiceJSON/EnumSchemas"
            params = {'session': self.token}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Получено схем: {len(data) if data else 0}")
                return data if data else []
            else:
                logger.error(f"❌ Ошибка получения схем: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Исключение при получении схем: {e}")
            return []

    def get_vehicles(self, schema_id: str) -> Dict:
        """Получение списка ТС с улучшенной обработкой"""
        try:
            if not self._ensure_auth():
                return {}

            url = f"{self.base_url}/ServiceJSON/EnumDevices"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                items_count = len(data.get('Items', [])) if data else 0
                logger.info(f"✅ Получено ТС: {items_count}")
                return data if data else {}
            else:
                logger.error(f"❌ Ошибка получения ТС: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Исключение при получении ТС: {e}")
            return {}

    def get_trips_total(self, schema_id: str, vehicle_id: str,
                        start_date: str, end_date: str,
                        trip_splitter_index: int = -1) -> Dict:
        """Получение информации о рейсах с улучшенной обработкой"""
        try:
            if not self._ensure_auth():
                return {}

            url = f"{self.base_url}/ServiceJSON/GetTripsTotal"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': vehicle_id,
                'SD': start_date,
                'ED': end_date,
                'tripSplitterIndex': trip_splitter_index
            }

            logger.info(f"🔄 Запрос рейсов для {vehicle_id} с {start_date} по {end_date}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if data and vehicle_id in data:
                    vehicle_data = data[vehicle_id]
                    trips_count = len(vehicle_data.get('Trips', []))
                    logger.info(f"✅ Получено рейсов для {vehicle_id}: {trips_count}")
                    return data
                else:
                    logger.warning(f"⚠️ Нет данных о рейсах для {vehicle_id}")
                    return {}
            else:
                logger.error(f"❌ Ошибка получения рейсов: {response.status_code}")
                return {}

        except requests.exceptions.Timeout:
            logger.error(f"⏰ Таймаут при получении рейсов для {vehicle_id}")
            return {}
        except Exception as e:
            logger.error(f"❌ Исключение при получении рейсов: {e}")
            return {}

    def get_online_info_all(self, schema_id: str) -> Dict:
        """Получение онлайн информации о всех ТС"""
        try:
            if not self._ensure_auth():
                return {}

            url = f"{self.base_url}/ServiceJSON/GetOnlineInfoAll"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Получены онлайн данные для {len(data)} ТС")
                return data if data else {}
            else:
                logger.error(f"❌ Ошибка получения онлайн данных: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Исключение при получении онлайн данных: {e}")
            return {}

    def get_track_data(self, schema_id: str, vehicle_id: str,
                       start_date: str, end_date: str) -> Dict:
        """Получение трека ТС с улучшенной обработкой"""
        try:
            if not self._ensure_auth():
                return {}

            url = f"{self.base_url}/ServiceJSON/GetTrack"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': vehicle_id,
                'SD': start_date,
                'ED': end_date,
                'tripSplitterIndex': -1
            }

            logger.info(f"🔄 Запрос трека для {vehicle_id}")
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                track_points = len(data.get(vehicle_id, [])) if data and vehicle_id in data else 0
                logger.info(f"✅ Получено точек трека для {vehicle_id}: {track_points}")
                return data if data else {}
            else:
                logger.error(f"❌ Ошибка получения трека: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"❌ Исключение при получении трека: {e}")
            return {}

    def format_date_for_api(self, date_string: str, is_start: bool = True) -> str:
        """Форматирование даты для API (yyyyMMdd-HHmm)"""
        try:
            # Если уже в правильном формате
            if len(date_string) == 13 and '-' in date_string and date_string[8] == '-':
                return date_string

            # Обработка различных форматов
            if 'T' in date_string:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            elif ' ' in date_string:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M')
            elif len(date_string) == 10:  # YYYY-MM-DD
                dt = datetime.strptime(date_string, '%Y-%m-%d')
            else:
                # Пробуем другие форматы
                try:
                    dt = datetime.fromisoformat(date_string)
                except:
                    dt = datetime.now()

            if is_start:
                return dt.strftime('%Y%m%d-0000')
            else:
                return dt.strftime('%Y%m%d-2359')

        except Exception as e:
            logger.error(f"❌ Ошибка форматирования даты {date_string}: {e}")
            today = datetime.now().strftime('%Y%m%d')
            return f"{today}-0000" if is_start else f"{today}-2359"

    def extract_license_plate(self, vehicle_data: Dict) -> str:
        """Извлечение госномера из данных ТС"""
        try:
            # Прямые поля
            possible_fields = ['VRN', 'LicensePlate', 'Госномер', 'RegNumber', 'VehicleRegNumber', 'Name']

            for field in possible_fields:
                value = vehicle_data.get(field)
                if value and isinstance(value, str) and value.strip() and value.strip().lower() != 'unknown':
                    return value.strip()

            # Поля в Properties
            properties = vehicle_data.get('Properties', [])
            for prop in properties:
                if prop.get('Name') in possible_fields:
                    value = prop.get('Value', '')
                    if value and str(value).strip() and str(value).strip().lower() != 'unknown':
                        return str(value).strip()

            return 'Не указан'

        except Exception as e:
            logger.error(f"❌ Ошибка извлечения госномера: {e}")
            return vehicle_data.get('Name', 'Не указан')