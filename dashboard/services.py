import requests
import logging
import warnings
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
logger = logging.getLogger(__name__)


class AutoGraphService:
    """Сервис для работы с AutoGRAPH API"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self, token=None):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'MonitoringApp/1.0'
        })
        self.session.verify = False

    def get_devices(self, schema_id):
        """Получить все устройства схемы"""
        if not self.token or not schema_id:
            return []

        try:
            url = f"{self.BASE_URL}/EnumDevices"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Ошибка получения устройств: HTTP {response.status_code}")
                return []

            devices_data = response.json()

            if not devices_data or 'Items' not in devices_data:
                return []

            devices = []
            for item in devices_data['Items']:
                try:
                    device_id = item.get('ID', '')
                    name = item.get('Name', f'ТС {device_id[:8]}')

                    # Ищем госномер
                    reg_num = "—"
                    properties = item.get('Properties', [])
                    for prop in properties:
                        if prop.get('Name') == 'VehicleRegNumber' and prop.get('Value'):
                            reg_num = prop['Value']
                            break

                    devices.append({
                        'id': device_id,
                        'name': name,
                        'reg_num': reg_num,
                        'serial': item.get('Serial', ''),
                    })

                except Exception as e:
                    logger.error(f"Ошибка обработки устройства: {e}")
                    continue

            return devices

        except Exception as e:
            logger.error(f"Ошибка получения устройств: {e}")
            return []

    def get_online_data(self, schema_id, device_ids):
        """Получить онлайн данные для устройств"""
        if not self.token or not schema_id or not device_ids:
            return {}

        try:
            if isinstance(device_ids, list):
                device_ids = ','.join(device_ids)

            url = f"{self.BASE_URL}/GetOnlineInfo"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_ids,
                'finalParams': '*',  # Запрашиваем ВСЕ финальные параметры для получения топлива
                'mchp': '0'
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Ошибка онлайн данных: HTTP {response.status_code}")
                return {}

            result = response.json()
            return result if isinstance(result, dict) else {}

        except Exception as e:
            logger.error(f"Ошибка получения онлайн данных: {e}")
            return {}

    # ==================== НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ТОПЛИВОМ ====================

    def get_device_parameters(self, schema_id, device_id):
        """Получить параметры устройства"""
        if not self.token or not schema_id or not device_id:
            return {}

        try:
            url = f"{self.BASE_URL}/EnumParameters"
            params = {
                'session': self.token,
                'schemaID': schema_id,
                'IDs': device_id
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code != 200:
                logger.error(f"Ошибка получения параметров: HTTP {response.status_code}")
                return {}

            result = response.json()
            return result if isinstance(result, dict) else {}

        except Exception as e:
            logger.error(f"Ошибка получения параметров: {e}")
            return {}

    def extract_fuel_data(self, online_data: Dict) -> Dict:
        """Извлечение данных о топливе из онлайн данных"""

        if not online_data:
            return {}

        fuel_data = {
            'total_volume': 0,  # Суммарный объем топлива в литрах
            'tank1_volume': 0,  # Объем в баке 1 (л)
            'tank2_volume': 0,  # Объем в баке 2 (л)
            'tank3_volume': 0,  # Объем в баке 3 (л)
            'fuel_level_percent': 0,  # Уровень топлива в %
            'fuel_remaining': 0,  # Остаток топлива (л)
            'fuel_consumed': 0,  # Расход топлива (л)
            'tanks_count': 0,  # Количество баков
            'has_fuel_data': False,  # Есть ли данные о топливе
            'raw_values': {}  # Сырые значения параметров
        }

        # Проверяем наличие данных Final
        if 'Final' in online_data and online_data['Final']:
            final_data = online_data['Final']

            # Собираем все значения, связанные с топливом
            for key, value in final_data.items():
                key_lower = key.lower()

                # Ищем параметры объема топлива (в литрах)
                if any(word in key_lower for word in ['fl1', 'дут1', 'tank1', 'бак1']):
                    try:
                        fuel_data['tank1_volume'] = float(value)
                        fuel_data['total_volume'] += fuel_data['tank1_volume']
                        fuel_data['tanks_count'] += 1
                        fuel_data['has_fuel_data'] = True
                    except (ValueError, TypeError):
                        pass

                elif any(word in key_lower for word in ['fl2', 'дут2', 'tank2', 'бак2']):
                    try:
                        fuel_data['tank2_volume'] = float(value)
                        fuel_data['total_volume'] += fuel_data['tank2_volume']
                        fuel_data['tanks_count'] += 1
                        fuel_data['has_fuel_data'] = True
                    except (ValueError, TypeError):
                        pass

                elif any(word in key_lower for word in ['fl3', 'дут3', 'tank3', 'бак3']):
                    try:
                        fuel_data['tank3_volume'] = float(value)
                        fuel_data['total_volume'] += fuel_data['tank3_volume']
                        fuel_data['tanks_count'] += 1
                        fuel_data['has_fuel_data'] = True
                    except (ValueError, TypeError):
                        pass

                # Общий уровень топлива
                elif any(word in key_lower for word in ['tankmain', 'общий', 'уровень', 'total']):
                    try:
                        volume = float(value)
                        # Если значение большое, вероятно это объем в литрах
                        if volume > 10:  # Предполагаем, что объем > 10 литров
                            fuel_data['total_volume'] = max(fuel_data['total_volume'], volume)
                            fuel_data['has_fuel_data'] = True
                    except (ValueError, TypeError):
                        pass

                # Уровень топлива в процентах
                elif 'level' in key_lower and ('fuel' in key_lower or 'топл' in key_lower):
                    try:
                        level = float(value)
                        if 0 <= level <= 100:  # Уровень в процентах
                            fuel_data['fuel_level_percent'] = level
                            fuel_data['has_fuel_data'] = True
                    except (ValueError, TypeError):
                        pass

                # Сохраняем сырое значение
                fuel_data['raw_values'][key] = value

        # Также проверяем основные поля
        for key in ['FuelLevel', 'TankMainFuelLevel', 'FuelRemaining', 'FuelConsumed']:
            if key in online_data:
                try:
                    value = float(online_data[key])
                    fuel_data['raw_values'][key] = value

                    if key == 'FuelLevel' and 0 <= value <= 100:
                        fuel_data['fuel_level_percent'] = value
                        fuel_data['has_fuel_data'] = True
                    elif key == 'TankMainFuelLevel' and value > 0:
                        fuel_data['total_volume'] = max(fuel_data['total_volume'], value)
                        fuel_data['has_fuel_data'] = True
                    elif key == 'FuelRemaining':
                        fuel_data['fuel_remaining'] = value
                        fuel_data['has_fuel_data'] = True
                    elif key == 'FuelConsumed':
                        fuel_data['fuel_consumed'] = value
                        fuel_data['has_fuel_data'] = True
                except (ValueError, TypeError):
                    pass

        return fuel_data

    def get_fuel_data_for_device(self, schema_id, device_id):
        """Получить данные о топливе для конкретного устройства"""

        # Получаем онлайн данные
        online_data_dict = self.get_online_data(schema_id, [device_id])

        if not online_data_dict or device_id not in online_data_dict:
            return {}

        online_data = online_data_dict[device_id]

        # Извлекаем данные о топливе
        fuel_data = self.extract_fuel_data(online_data)

        # Если нет данных, пробуем получить параметры для более точного запроса
        if not fuel_data['has_fuel_data']:
            # Получаем параметры устройства
            params_data = self.get_device_parameters(schema_id, device_id)

            if params_data and device_id in params_data:
                device_params = params_data[device_id]

                # Ищем параметры топлива в конфигурации
                fuel_param_names = []

                # Проверяем FinalParams
                for param in device_params.get('FinalParams', []):
                    name = param.get('Name', '')
                    caption = param.get('Caption', '')

                    search_str = (name + caption).lower()
                    if any(word in search_str for word in
                           ['fuel', 'топл', 'бак', 'tank', 'расход', 'level', 'уровень']):
                        fuel_param_names.append(name)

                # Если нашли параметры топлива, делаем целевой запрос
                if fuel_param_names:
                    fuel_params_str = ','.join(fuel_param_names[:10])  # Ограничиваем количество

                    # Делаем запрос с конкретными параметрами топлива
                    url = f"{self.BASE_URL}/GetOnlineInfo"
                    params = {
                        'session': self.token,
                        'schemaID': schema_id,
                        'IDs': device_id,
                        'finalParams': fuel_params_str,
                        'mchp': '0'
                    }

                    try:
                        response = self.session.get(url, params=params, timeout=30)
                        if response.status_code == 200:
                            fuel_response = response.json()
                            if fuel_response and device_id in fuel_response:
                                fuel_online_data = fuel_response[device_id]
                                fuel_data = self.extract_fuel_data(fuel_online_data)
                    except Exception as e:
                        logger.error(f"Ошибка запроса данных топлива: {e}")

        return fuel_data

    def get_all_fuel_data(self, schema_id, device_ids=None):
        """Получить данные о топливе для всех устройств или указанных"""

        if not device_ids:
            # Получаем все устройства
            devices = self.get_devices(schema_id)
            device_ids = [d['id'] for d in devices]

        # Получаем онлайн данные для всех устройств
        online_data_dict = self.get_online_data(schema_id, device_ids)

        if not online_data_dict:
            return {}

        # Обрабатываем данные для каждого устройства
        fuel_report = {
            'total_fuel_volume': 0,  # Суммарный объем топлива по всем ТС
            'devices_with_fuel': 0,  # Количество ТС с данными о топливе
            'total_tanks': 0,  # Общее количество баков
            'devices': {}  # Данные по каждому устройству
        }

        for device_id in device_ids:
            if device_id in online_data_dict:
                online_data = online_data_dict[device_id]
                fuel_data = self.extract_fuel_data(online_data)

                # Находим имя устройства
                device_name = online_data.get('name', f'ТС {device_id[:8]}')

                # Форматируем данные для отображения
                device_fuel_info = {
                    'name': device_name,
                    'has_fuel_data': fuel_data['has_fuel_data'],
                    'total_volume': round(fuel_data['total_volume'], 1),
                    'fuel_level_percent': round(fuel_data['fuel_level_percent'], 1),
                    'fuel_remaining': round(fuel_data['fuel_remaining'], 1),
                    'fuel_consumed': round(fuel_data['fuel_consumed'], 1),
                    'tanks_count': fuel_data['tanks_count'],
                    'tank1_volume': round(fuel_data['tank1_volume'], 1),
                    'tank2_volume': round(fuel_data['tank2_volume'], 1),
                    'tank3_volume': round(fuel_data['tank3_volume'], 1),
                    'raw_values': fuel_data['raw_values']
                }

                # Суммируем статистику
                if fuel_data['has_fuel_data']:
                    fuel_report['devices_with_fuel'] += 1
                    fuel_report['total_fuel_volume'] += fuel_data['total_volume']
                    fuel_report['total_tanks'] += fuel_data['tanks_count']

                fuel_report['devices'][device_id] = device_fuel_info

        return fuel_report