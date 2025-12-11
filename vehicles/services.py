import logging
import requests
import warnings
import time
from typing import Dict, List, Any
from datetime import datetime

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
logger = logging.getLogger(__name__)


class AutoGraphHistoricalService:
    """Улучшенный сервис для работы с историческими данными AutoGRAPH API"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self, token=None, schema_id=None):
        self.token = token
        self.schema_id = schema_id
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'MonitoringApp/2.0'
        })
        self.session.verify = False
        self.request_timeout = 300

        # Полный список всех параметров для временных рядов
        self.ALL_PARAMETERS = [
            # Скорость и движение
            "Speed", "MaxSpeed", "AverageSpeed", "SpeedLimit", "OverspeedCount",
            "TotalDistance", "MoveDuration", "ParkDuration", "ParkCount",

            # Топливо
            "Engine1FuelConsum", "TankMainFuelLevel", "TankMainFuelLevel First",
            "TankMainFuelLevel Last", "TankMainFuelUpVol Diff", "TankMainFuelDnVol Diff",
            "Engine1FuelConsumMPer100km", "Engine1FuelConsumP/M",
            "Engine1FuelConsumDuringMH", "Engine1FuelConsumP/MDuringMH",

            # Двигатель
            "Engine1Motohours", "Engine1MHOnParks", "Engine1MHInMove", "EngineRPM",
            "EngineTemperature", "EngineOilPressure",

            # Координаты и GPS
            "Longitude", "Latitude", "Altitude", "Course", "GPSSatellites", "GPSHDOP",

            # Качество вождения
            "DQRating", "DQOverspeedPoints Diff", "DQExcessAccelPoints Diff",
            "DQExcessBrakePoints Diff", "DQEmergencyBrakePoints Diff",
            "DQExcessRightPoints Diff", "DQExcessLeftPoints Diff", "DQExcessBumpPoints Diff",
            "DQPoints Diff",

            # Время и работа
            "TotalDuration", "WorkTime", "IdleTime", "Duration",

            # Сигнал и питание
            "GSMLevel", "PowerVoltage", "InternalTemperature",

            # CAN-данные
            "CAN_Speed", "CAN_RPM", "CAN_FuelLevel", "CAN_OilPressure", "CAN_Temperature",

            # Датчики
            "Temperature1", "Temperature2", "Temperature3", "Pressure1", "Pressure2",
            "AnalogInput1", "AnalogInput2", "AnalogInput3", "AnalogInput4"
        ]

    def get_extended_historical_data(self, device_ids: List[str], start_date: str, end_date: str) -> Dict:
        """
        Получение расширенных исторических данных для временных рядов
        """
        if not self.token or not self.schema_id or not device_ids:
            logger.error("Отсутствуют необходимые параметры")
            return {}

        try:
            # Форматируем даты
            start_fmt = start_date.replace('-', '')
            end_fmt = end_date.replace('-', '') + '-2359'

            logger.info(f"📊 Запрос расширенных исторических данных:")
            logger.info(f"  - ТС: {len(device_ids)} шт")
            logger.info(f"  - Период: {start_date} - {end_date}")

            # 1. Получаем ВСЕ данные через GetTripItems
            logger.info("1️⃣ Получение ВСЕХ данных через GetTripItems...")
            all_data = self._get_complete_trip_items_data(device_ids, start_fmt, end_fmt)

            if not all_data:
                logger.warning("❌ Не удалось получить данные через GetTripItems")
                return self._get_fallback_data(device_ids, start_date, end_date)

            # 2. Получаем данные через GetTripsTotal для сводки
            logger.info("2️⃣ Получение сводных данных GetTripsTotal...")
            summary_data = self._get_trips_total_data(device_ids, start_fmt, end_fmt)

            # 3. Форматируем для временных рядов (БЕЗ ОГРАНИЧЕНИЯ НА 1000 ЗАПИСЕЙ)
            logger.info("3️⃣ Форматирование данных для временных рядов...")
            processed_data = self._format_for_timeseries_full(
                all_data=all_data,
                summary_data=summary_data,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"✅ Данные успешно обработаны: {processed_data.get('total_records', 0)} записей")
            return processed_data

        except Exception as e:
            logger.error(f"❌ Ошибка получения расширенных данных: {e}", exc_info=True)
            return self._get_fallback_data(device_ids, start_date, end_date)

    def _format_for_timeseries_full(self, all_data: Dict, summary_data: Dict,
                                  start_date: str, end_date: str) -> Dict:
        """Форматирование данных для временных рядов (БЕЗ ОГРАНИЧЕНИЙ)"""
        processed_data = {
            'time_series': [],
            'summary': {},
            'vehicle_info': {},
            'parameters': [],
            'total_records': 0,
            'period': {'start': start_date, 'end': end_date},
            'data_type': 'time_series_extended'
        }

        if not all_data or not isinstance(all_data, dict):
            logger.warning("⚠️ Нет данных для форматирования")
            return processed_data

        total_records = 0

        for device_id, device_data in all_data.items():
            try:
                if not device_data or not isinstance(device_data, dict):
                    logger.warning(f"⚠️ Пропускаем некорректные данные ТС {device_id}")
                    continue

                vehicle_name = device_data.get('Name', f'ТС {device_id[:8]}')
                params = device_data.get('Params', [])
                items = device_data.get('Items', [])

                if not items:
                    logger.debug(f"⚠️ Нет записей для ТС {vehicle_name}")
                    continue

                processed_data['vehicle_info'][device_id] = {
                    'name': vehicle_name,
                    'param_count': len(params),
                    'item_count': len(items)
                }

                if params and isinstance(params, list):
                    for param in params:
                        if param and param not in processed_data['parameters']:
                            processed_data['parameters'].append(param)

                # ВАЖНО: УБИРАЕМ ОГРАНИЧЕНИЕ НА 1000 ЗАПИСЕЙ
                for item in items:  # Без [:1000]
                    if not item or not isinstance(item, dict):
                        continue

                    time_point = self._create_time_point(item, params, vehicle_name, device_id)
                    if time_point:
                        processed_data['time_series'].append(time_point)
                        total_records += 1

                logger.info(f"✅ Обработан ТС {vehicle_name}: {len(items)} записей, {len(params)} параметров")

            except Exception as e:
                logger.error(f"❌ Ошибка обработки ТС {device_id}: {e}")

        processed_data['time_series'].sort(key=lambda x: x.get('timestamp', ''))
        processed_data['total_records'] = total_records

        processed_data['summary'] = self._create_timeseries_summary(
            processed_data['time_series'],
            summary_data
        )

        logger.info(f"📊 Итог: {total_records} записей, {len(processed_data['parameters'])} параметров")
        return processed_data

    def _get_fallback_data(self, device_ids: List[str], start_date: str, end_date: str) -> Dict:
        """Получение данных fallback способом для совместимости"""
        logger.info("🔄 Использование fallback метода получения данных...")

        try:
            # Используем минимальный набор параметров
            basic_params = [
                "Speed", "MaxSpeed", "AverageSpeed", "TotalDistance",
                "Engine1FuelConsum", "Engine1Motohours", "DQRating",
                "MoveDuration", "ParkDuration", "OverspeedCount"
            ]

            start_fmt = start_date.replace('-', '')
            end_fmt = end_date.replace('-', '') + '-2359'

            data = self._get_trip_items_data_with_params(
                device_ids=device_ids,
                start_fmt=start_fmt,
                end_fmt=end_fmt,
                params=basic_params
            )

            if not data:
                return self._create_empty_response(start_date, end_date)

            # Форматируем минимальные данные
            processed_data = {
                'time_series': [],
                'summary': {},
                'vehicle_info': {},
                'parameters': [],
                'total_records': 0,
                'period': {'start': start_date, 'end': end_date},
                'data_type': 'fallback_basic'
            }

            for device_id, device_data in data.items():
                if not device_data:
                    continue

                vehicle_name = device_data.get('Name', f'ТС {device_id[:8]}')
                params = device_data.get('Params', [])
                items = device_data.get('Items', [])

                processed_data['vehicle_info'][device_id] = {
                    'name': vehicle_name,
                    'param_count': len(params),
                    'item_count': len(items)
                }

                # Обрабатываем записи (БЕЗ ОГРАНИЧЕНИЙ)
                for item in items:  # Без [:100]
                    time_point = self._create_time_point(item, params, vehicle_name, device_id)
                    if time_point:
                        processed_data['time_series'].append(time_point)

            processed_data['time_series'].sort(key=lambda x: x.get('timestamp', ''))
            processed_data['total_records'] = len(processed_data['time_series'])

            # Создаем простую сводку
            if processed_data['time_series']:
                processed_data['summary'] = {
                    'total_records': processed_data['total_records'],
                    'vehicle_count': len(processed_data['vehicle_info']),
                    'time_range': {
                        'first': processed_data['time_series'][0].get('timestamp'),
                        'last': processed_data['time_series'][-1].get('timestamp') if processed_data[
                            'time_series'] else None
                    }
                }

            logger.info(f"✅ Fallback данные получены: {processed_data['total_records']} записей")
            return processed_data

        except Exception as e:
            logger.error(f"❌ Ошибка fallback метода: {e}")
            return self._create_empty_response(start_date, end_date)

    def _create_empty_response(self, start_date: str, end_date: str) -> Dict:
        """Создание пустого ответа"""
        return {
            'time_series': [],
            'summary': {
                'total_records': 0,
                'vehicle_count': 0,
                'time_range': {'start': start_date, 'end': end_date}
            },
            'vehicle_info': {},
            'parameters': [],
            'total_records': 0,
            'period': {'start': start_date, 'end': end_date},
            'data_type': 'empty',
            'notes': 'Нет данных для указанного периода'
        }

    def _get_complete_trip_items_data(self, device_ids: List[str], start_fmt: str, end_fmt: str) -> Dict:
        """
        Получаем полные данные через GetTripItems с оптимизацией
        """
        # Разбиваем на группы по 50 параметров для избежания превышения лимита URL
        param_groups = self._split_parameters_into_groups(self.ALL_PARAMETERS, group_size=50)

        all_data = {}

        for i, param_group in enumerate(param_groups):
            logger.info(f"📦 Запрос группы параметров {i + 1}/{len(param_groups)} ({len(param_group)} параметров)")

            data = self._get_trip_items_data_with_params(
                device_ids=device_ids,
                start_fmt=start_fmt,
                end_fmt=end_fmt,
                params=param_group
            )

            if not data:
                logger.warning(f"❌ Группа параметров {i + 1} не вернула данных")
                continue

            # Объединяем данные
            self._merge_trip_items_data(all_data, data)

            time.sleep(0.5)

        return all_data if all_data else None

    def _get_trip_items_data_with_params(self, device_ids: List[str], start_fmt: str,
                                         end_fmt: str, params: List[str]) -> Dict:
        """Получаем данные с конкретными параметрами"""
        url = f"{self.BASE_URL}/GetTripItems"

        params_str = ','.join(params)

        request_params = {
            'session': self.token,
            'schemaID': self.schema_id,
            'IDs': ','.join(device_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0,
            'tripParams': params_str,
            'stage': 'Motion,Idle,Parking,Unknown'
        }

        try:
            logger.debug(f"Отправка запроса с параметрами: {len(params)} шт")
            response = self.session.get(url, params=request_params, timeout=90)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    logger.debug(f"✅ Получены данные для {len(data)} ТС")
                    return data
                else:
                    logger.warning(f"⚠️ Данные пустые или в неверном формате")
                    return {}
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                return {}

        except requests.exceptions.Timeout:
            logger.error(f"❌ Таймаут запроса")
            return {}
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            return {}

    def _merge_trip_items_data(self, main_data: Dict, new_data: Dict):
        """Объединение данных из нескольких запросов"""
        if not new_data or not isinstance(new_data, dict):
            logger.warning("⚠️ Попытка объединить пустые или некорректные данные")
            return

        for device_id, device_data in new_data.items():
            if not device_data or not isinstance(device_data, dict):
                logger.warning(f"⚠️ Пропускаем некорректные данные для ТС {device_id}")
                continue

            if device_id not in main_data:
                main_data[device_id] = {
                    'Name': device_data.get('Name', f'ТС {device_id[:8]}'),
                    'Params': [],
                    'Items': []
                }

            existing_params = main_data[device_id]['Params']
            new_params = device_data.get('Params', [])

            if new_params and isinstance(new_params, list):
                for param in new_params:
                    if param not in existing_params:
                        existing_params.append(param)

            existing_items = main_data[device_id]['Items']
            new_items = device_data.get('Items', [])

            if not existing_items and new_items:
                main_data[device_id]['Items'] = new_items.copy()
            elif existing_items and new_items and len(existing_items) == len(new_items):
                for i, (existing_item, new_item) in enumerate(zip(existing_items, new_items)):
                    if i < len(new_item.get('Values', [])):
                        existing_item['Values'].extend(new_item['Values'])

    def _create_time_point(self, item: Dict, params: List[str],
                           vehicle_name: str, device_id: str) -> Dict:
        """Создание точки временного ряда"""
        if not item or not isinstance(item, dict):
            return None

        timestamp = item.get('DT', '')
        if not timestamp:
            return None

        time_point = {
            'timestamp': timestamp,
            'vehicle_id': device_id,
            'vehicle_name': vehicle_name,
            'stage': item.get('Stage', 'Unknown'),
            'duration': item.get('Duration', ''),
            'caption': item.get('Caption', ''),
            'values': {},
            'raw_values': item.get('Values', [])
        }

        values = item.get('Values', [])
        if values and isinstance(values, list):
            for i, param in enumerate(params):
                if i < len(values):
                    value = values[i]
                    numeric_value = self._parse_numeric_value(value)

                    if numeric_value is not None:
                        time_point['values'][param] = numeric_value
                    else:
                        time_point['values'][param] = value

        return time_point

    def _create_timeseries_summary(self, time_series: List[Dict], summary_data: Dict) -> Dict:
        """Создание сводки для временных рядов"""
        summary = {
            'total_records': len(time_series),
            'vehicle_count': len(set(p.get('vehicle_id', '') for p in time_series if p.get('vehicle_id'))),
            'time_range': {},
            'parameter_stats': {},
            'vehicle_stats': {}
        }

        if not time_series:
            return summary

        timestamps = [p.get('timestamp', '') for p in time_series if p.get('timestamp')]
        if timestamps:
            summary['time_range']['first'] = min(timestamps)
            summary['time_range']['last'] = max(timestamps)

        all_params = set()
        for point in time_series:
            if point.get('values'):
                all_params.update(point['values'].keys())

        for param in all_params:
            values = []
            for point in time_series:
                if param in point.get('values', {}):
                    value = point['values'][param]
                    if isinstance(value, (int, float)):
                        values.append(value)

            if values:
                summary['parameter_stats'][param] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'sum': sum(values)
                }

        vehicles = {}
        for point in time_series:
            vehicle_id = point.get('vehicle_id')
            if vehicle_id:
                if vehicle_id not in vehicles:
                    vehicles[vehicle_id] = {
                        'name': point.get('vehicle_name', ''),
                        'record_count': 0,
                        'params': set()
                    }
                vehicles[vehicle_id]['record_count'] += 1
                if point.get('values'):
                    vehicles[vehicle_id]['params'].update(point['values'].keys())

        for vehicle_id, stats in vehicles.items():
            summary['vehicle_stats'][vehicle_id] = {
                'name': stats['name'],
                'record_count': stats['record_count'],
                'param_count': len(stats['params'])
            }

        return summary

    def _split_parameters_into_groups(self, parameters: List[str], group_size: int = 50) -> List[List[str]]:
        """Разбиваем параметры на группы для избежания превышения лимита URL"""
        groups = []
        for i in range(0, len(parameters), group_size):
            groups.append(parameters[i:i + group_size])

        logger.info(f"📊 Параметры разбиты на {len(groups)} групп по {group_size} параметров")
        return groups

    def _get_trips_total_data(self, device_ids: List[str], start_fmt: str, end_fmt: str) -> Dict:
        """Получаем сводные данные через GetTripsTotal"""
        url = f"{self.BASE_URL}/GetTripsTotal"
        params = {
            'session': self.token,
            'schemaID': self.schema_id,
            'IDs': ','.join(device_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"❌ GetTripsTotal ошибка: {e}")

        return {}

    def get_historical_data(self, device_ids: List[str], start_date: str, end_date: str) -> Dict:
        """
        Совместимый метод для получения исторических данных
        (сохраняем для обратной совместимости)
        """
        return self.get_extended_historical_data(device_ids, start_date, end_date)

    def _parse_numeric_value(self, value):
        """Парсинг числового значения"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                clean_value = value.replace(',', '.').strip()
                if clean_value == '':
                    return None
                return float(clean_value)
            except:
                return None

        return None

    def _time_str_to_hours(self, time_str: str) -> float:
        """Преобразует строку времени (HH:MM:SS) в часы"""
        if not time_str:
            return 0.0

        try:
            parts = time_str.split(':')
            hours = float(parts[0]) if len(parts) > 0 else 0
            minutes = float(parts[1]) if len(parts) > 1 else 0
            seconds = float(parts[2]) if len(parts) > 2 else 0

            return hours + minutes / 60 + seconds / 3600
        except:
            return 0.0


class AutoGraphDeviceService:
    """Сервис для работы с устройствами AutoGRAPH"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self, token=None):
        self.token = token
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'DeviceService/2.0'
        })

    def get_devices(self, schema_id: str) -> List[Dict]:
        """Получение списка устройств"""
        try:
            if not self.token or not schema_id:
                logger.error("Нет токена или ID схемы")
                return []

            devices_url = f"{self.BASE_URL}/EnumDevices"
            params = {
                'session': self.token,
                'schemaID': schema_id
            }

            logger.info(f"Запрос устройств через EnumDevices: schemaID={schema_id}")
            response = self.session.get(devices_url, params=params, timeout=15)

            if response.status_code != 200:
                logger.error(f"Ошибка получения устройств: HTTP {response.status_code}")
                return []

            devices_data = response.json()

            devices = []

            if isinstance(devices_data, dict) and 'Items' in devices_data:
                devices_list = devices_data['Items']
            elif isinstance(devices_data, list):
                devices_list = devices_data
            else:
                logger.error(f"Неожиданный формат данных устройств: {type(devices_data)}")
                return []

            for device in devices_list:
                if not isinstance(device, dict):
                    continue

                reg_num = ""
                if 'Properties' in device and isinstance(device['Properties'], list):
                    for prop in device['Properties']:
                        if isinstance(prop, dict) and prop.get('Name') == 'VehicleRegNumber':
                            reg_num = prop.get('Value', '')
                            break

                devices.append({
                    'id': device.get('ID', ''),
                    'name': device.get('Name', ''),
                    'reg_num': reg_num or device.get('RegNum', ''),
                    'serial': device.get('Serial', ''),
                    'model': device.get('Model', ''),
                    'phone': device.get('Phone', ''),
                    'driver': device.get('Driver', '')
                })

            logger.info(f"✅ Успешно получено {len(devices)} устройств")
            return devices

        except Exception as e:
            logger.error(f"Ошибка получения устройств: {e}", exc_info=True)
            return []