# vehicles/services.py
import logging
import requests
import warnings
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import math

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
logger = logging.getLogger(__name__)


class AutoGraphHistoricalService:
    """Сервис для работы с историческими данными AutoGRAPH API"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self, token=None, schema_id=None):
        self.token = token
        self.schema_id = schema_id
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'MonitoringApp/1.0'
        })
        self.session.verify = False
        self.request_timeout = 300

    def get_historical_data(self, device_ids: List[str], start_date: str, end_date: str) -> Dict:
        """
        Получение исторических данных ТРЕМЯ способами для сравнения
        Возвращает данные в СОВМЕСТИМОМ формате для фронтенда
        """
        if not self.token or not self.schema_id or not device_ids:
            logger.error("Отсутствуют необходимые параметры")
            return {}

        try:
            # Форматируем даты
            start_fmt = start_date.replace('-', '')  # YYYYMMDD
            end_fmt = end_date.replace('-', '') + '-2359'  # YYYYMMDD-HHMM

            logger.info(f"📊 Запрос исторических данных:")
            logger.info(f"  - ТС: {len(device_ids)} шт")
            logger.info(f"  - Период: {start_date} - {end_date}")

            # 1. Получаем данные через GetTripsOnly (готовые данные)
            logger.info("1️⃣ Получение данных GetTripsOnly...")
            trips_only_data = self._get_trips_only_data(device_ids, start_fmt, end_fmt)

            # 2. Получаем данные через GetTripItems (сырые данные для графиков)
            logger.info("2️⃣ Получение данных GetTripItems...")
            trip_items_data = self._get_trip_items_data(device_ids, start_fmt, end_fmt, stage='Motion')

            # 3. Получаем данные через GetTripsTotal (итоговые данные)
            logger.info("3️⃣ Получение данных GetTripsTotal...")
            trips_total_data = self._get_trips_total_data(device_ids, start_fmt, end_fmt)

            # Объединяем все данные в СОВМЕСТИМЫЙ формат
            logger.info("🔄 Объединение данных для фронтенда...")
            processed_data = self._merge_data_for_frontend(
                trips_only_data=trips_only_data,
                trip_items_data=trip_items_data,
                trips_total_data=trips_total_data,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"✅ Данные успешно обработаны")
            return processed_data

        except Exception as e:
            logger.error(f"❌ Ошибка получения исторических данных: {e}", exc_info=True)
            return {}

    def _merge_data_for_frontend(self, trips_only_data: Dict, trip_items_data: Dict,
                                 trips_total_data: Dict, start_date: str, end_date: str) -> Dict:
        """Объединяем данные для фронтенда в СОВМЕСТИМОМ формате"""
        processed_data = {
            'vehicles': {},
            'summary': {},
            'chart_data': {},
            'total_stages': 0,
            'available_parameters': [],
            'period': {'start': start_date, 'end': end_date},
            'data_type': 'mixed',
            'sources': ['GetTripsOnly', 'GetTripItems', 'GetTripsTotal'],
            'notes': 'Данные получены из трех источников API Autograf'
        }

        # Собираем все ID устройств
        all_device_ids = set()
        all_device_ids.update(trips_only_data.keys())
        all_device_ids.update(trip_items_data.keys())
        all_device_ids.update(trips_total_data.keys())

        total_stages = 0

        for device_id in all_device_ids:
            try:
                # Получаем имя ТС
                vehicle_name = self._get_vehicle_name(device_id, trips_only_data, trip_items_data, trips_total_data)

                # Извлекаем статистику
                trips_only_stats = self._extract_trips_only_stats(device_id, trips_only_data)
                trip_items_stats, raw_stages = self._extract_trip_items_stats(device_id, trip_items_data)
                trips_total_stats = self._extract_trips_total_stats(device_id, trips_total_data)

                # Создаем сводку
                summary = self._create_vehicle_summary(trips_only_stats, trip_items_stats)

                # Сохраняем параметры (из первого ТС)
                if trip_items_data.get(device_id) and 'Params' in trip_items_data[device_id]:
                    params = trip_items_data[device_id]['Params']
                    if not processed_data['available_parameters']:
                        processed_data['available_parameters'] = params

                total_stages += len(raw_stages)

                processed_data['vehicles'][device_id] = {
                    'id': device_id,
                    'name': vehicle_name,
                    'trips_only_stats': trips_only_stats,
                    'trip_items_stats': trip_items_stats,
                    'trips_total_stats': trips_total_stats,
                    'summary': summary,
                    'raw_stages': raw_stages
                }

                logger.debug(f"✅ ТС {vehicle_name} обработан: {len(raw_stages)} стадий")

            except Exception as e:
                logger.error(f"❌ Ошибка обработки ТС {device_id}: {e}")

        # Создаем общую статистику
        processed_data['summary'] = self._create_overall_summary(processed_data['vehicles'])
        processed_data['total_stages'] = total_stages

        logger.info(f"✅ Обработка завершена: {len(processed_data['vehicles'])} ТС, {total_stages} стадий")
        return processed_data

    def _get_trips_only_data(self, device_ids: List[str], start_fmt: str, end_fmt: str) -> Dict:
        """Получаем готовые данные через GetTripsOnly"""
        url = f"{self.BASE_URL}/GetTripsOnly"
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
                data = response.json()
                logger.info(f"✅ GetTripsOnly: получено данных для {len(data)} ТС")
                return data
            else:
                logger.error(f"❌ GetTripsOnly: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"❌ GetTripsOnly ошибка: {e}")

        return {}

    def _get_trip_items_data(self, device_ids: List[str], start_fmt: str, end_fmt: str, stage: str = None) -> Dict:
        """Получаем сырые данные через GetTripItems"""
        # Параметры для получения
        params_list = [
            "TotalDistance", "MaxSpeed", "AverageSpeed", "Engine1FuelConsum",
            "Engine1FuelConsumM", "Engine1FuelConsumP", "OverspeedCount",
            "TankMainFuelLevel First", "TankMainFuelLevel Last", "Engine1Motohours",
            "MoveDuration", "ParkDuration", "TotalDuration", "DQRating", "ParkCount",
            "DateTime First", "DateTime Last", "FirstLocation", "LastLocation"
        ]

        url = f"{self.BASE_URL}/GetTripItems"
        params = {
            'session': self.token,
            'schemaID': self.schema_id,
            'IDs': ','.join(device_ids),
            'SD': start_fmt,
            'ED': end_fmt,
            'tripSplitterIndex': 0,
            'tripParams': ','.join(params_list)
        }

        if stage:
            params['stage'] = stage

        try:
            response = self.session.get(url, params=params, timeout=60)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ GetTripItems: получено данных для {len(data)} ТС")
                return data
            else:
                logger.error(f"❌ GetTripItems: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"❌ GetTripItems ошибка: {e}")

        return {}

    def _get_trips_total_data(self, device_ids: List[str], start_fmt: str, end_fmt: str) -> Dict:
        """Получаем итоговые данные через GetTripsTotal"""
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
                data = response.json()
                logger.info(f"✅ GetTripsTotal: получено данных для {len(data)} ТС")
                return data
            else:
                logger.error(f"❌ GetTripsTotal: HTTP {response.status_code}")

        except Exception as e:
            logger.error(f"❌ GetTripsTotal ошибка: {e}")

        return {}

    def _get_vehicle_name(self, device_id: str, *data_sources) -> str:
        """Получаем имя ТС из любого источника"""
        for source in data_sources:
            if isinstance(source, dict) and device_id in source:
                vehicle_data = source[device_id]
                if isinstance(vehicle_data, dict):
                    return vehicle_data.get('Name', f'ТС {device_id[:8]}')
        return f'ТС {device_id[:8]}'

    def _extract_trips_only_stats(self, device_id: str, trips_only_data: Dict) -> Dict:
        """Извлекаем статистику из GetTripsOnly"""
        stats = {
            'trip_count': 0,
            'total_distance': 0.0,
            'total_fuel': 0.0,
            'max_speed': 0.0,
            'avg_speed': 0.0,
            'motohours': 0.0,
            'move_duration': 0.0,
            'park_duration': 0.0,
            'park_count': 0,
            'overspeed_count': 0,
            'fuel_level_start': 0.0,
            'fuel_level_end': 0.0,
            'trips': []
        }

        if device_id in trips_only_data:
            vehicle_data = trips_only_data[device_id]

            if 'Trips' in vehicle_data and isinstance(vehicle_data['Trips'], list):
                trips = vehicle_data['Trips']
                stats['trip_count'] = len(trips)

                for trip in trips:
                    if 'Total' in trip and isinstance(trip['Total'], dict):
                        total = trip['Total']

                        trip_info = {
                            'date': trip.get('SD', ''),
                            'start_time': total.get('DateTime First', ''),
                            'end_time': total.get('DateTime Last', ''),
                            'distance': self._parse_numeric_value(total.get('TotalDistance', 0)),
                            'fuel': self._parse_numeric_value(total.get('Engine1FuelConsum', 0)),
                            'max_speed': self._parse_numeric_value(total.get('MaxSpeed', 0)),
                            'avg_speed': self._parse_numeric_value(total.get('AverageSpeed', 0)),
                            'motohours': self._time_str_to_hours(total.get('Engine1Motohours', '00:00:00')),
                            'move_duration': self._time_str_to_hours(total.get('MoveDuration', '00:00:00')),
                            'park_duration': self._time_str_to_hours(total.get('ParkDuration', '00:00:00')),
                            'park_count': int(total.get('ParkCount', 0)),
                            'overspeed_count': int(total.get('OverspeedCount', 0))
                        }

                        # Суммируем статистику
                        stats['total_distance'] += trip_info['distance'] or 0
                        stats['total_fuel'] += trip_info['fuel'] or 0
                        stats['max_speed'] = max(stats['max_speed'], trip_info['max_speed'] or 0)

                        if trip_info['distance'] and trip_info['avg_speed']:
                            stats['avg_speed'] = (stats['avg_speed'] * len(stats['trips']) + trip_info['avg_speed']) / (
                                        len(stats['trips']) + 1)

                        stats['motohours'] += trip_info['motohours'] or 0
                        stats['move_duration'] += trip_info['move_duration'] or 0
                        stats['park_duration'] += trip_info['park_duration'] or 0
                        stats['park_count'] += trip_info['park_count'] or 0
                        stats['overspeed_count'] += trip_info['overspeed_count'] or 0

                        stats['trips'].append(trip_info)

        # Округляем значения
        for key in ['total_distance', 'total_fuel', 'max_speed', 'avg_speed', 'motohours',
                    'move_duration', 'park_duration']:
            if key in stats:
                stats[key] = round(stats[key] or 0, 2)

        return stats

    def _extract_trip_items_stats(self, device_id: str, trip_items_data: Dict) -> Tuple[Dict, List]:
        """Извлекаем статистику и сырые данные из GetTripItems"""
        stats = {
            'stage_count': 0,
            'daily_data': {},
            'hourly_data': {},
            'stage_types': {},
            'statistics': {},
            'raw_stages': []
        }

        raw_stages = []

        if device_id in trip_items_data:
            vehicle_data = trip_items_data[device_id]

            # Получаем список параметров
            params = vehicle_data.get('Params', [])
            items = vehicle_data.get('Items', [])

            stats['stage_count'] = len(items)

            # Статистика по параметрам
            param_stats = {}

            # Обрабатываем каждую запись
            for item in items:
                # Базовые данные
                stage = item.get('Stage', 'Unknown')
                dt = item.get('DT', '')
                duration = item.get('Duration', '')
                caption = item.get('Caption', '')
                values = item.get('Values', [])

                # Извлекаем дату
                date_key = ''
                if 'T' in dt:
                    date_key = dt.split('T')[0]
                elif ' ' in dt:
                    date_key = dt.split(' ')[0]
                else:
                    date_key = dt[:10] if len(dt) >= 10 else dt

                # Создаем запись сырых данных
                raw_stage = {
                    'stage': stage,
                    'dt': dt,
                    'duration': duration,
                    'caption': caption,
                    'date': date_key,
                    'raw_values': {}
                }

                # Извлекаем значения параметров
                for i, param in enumerate(params):
                    if i < len(values):
                        value = values[i]
                        # Преобразуем в число если возможно
                        num_value = self._parse_numeric_value(value)
                        raw_stage[param] = num_value if num_value is not None else value
                        raw_stage['raw_values'][param] = value

                        # Собираем статистику по параметрам
                        if num_value is not None:
                            if param not in param_stats:
                                param_stats[param] = []
                            param_stats[param].append(num_value)

                # Считаем типы стадий
                if stage not in stats['stage_types']:
                    stats['stage_types'][stage] = 0
                stats['stage_types'][stage] += 1

                raw_stages.append(raw_stage)

            # Рассчитываем статистику по параметрам
            for param, values in param_stats.items():
                if values:
                    stats['statistics'][param] = {
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'sum': sum(values),
                        'count': len(values)
                    }

        stats['raw_stages'] = raw_stages
        return stats, raw_stages

    def _extract_trips_total_stats(self, device_id: str, trips_total_data: Dict) -> Dict:
        """Извлекаем статистику из GetTripsTotal"""
        stats = {
            'total_distance': 0.0,
            'total_fuel': 0.0,
            'max_speed': 0.0,
            'avg_speed': 0.0,
            'overspeed_count': 0,
            'park_count': 0,
            'motohours': 0.0,
            'move_duration': 0.0,
            'park_duration': 0.0
        }

        if device_id in trips_total_data:
            vehicle_data = trips_total_data[device_id]

            # Проверяем разные структуры
            total_data = None

            if 'Total' in vehicle_data:
                total_data = vehicle_data['Total']
            elif 'Trips' in vehicle_data and vehicle_data['Trips']:
                trip = vehicle_data['Trips'][0]
                if 'Total' in trip:
                    total_data = trip['Total']

            if isinstance(total_data, dict):
                stats['total_distance'] = self._parse_numeric_value(total_data.get('TotalDistance', 0)) or 0
                stats['total_fuel'] = self._parse_numeric_value(total_data.get('Engine1FuelConsum', 0)) or 0
                stats['max_speed'] = self._parse_numeric_value(total_data.get('MaxSpeed', 0)) or 0
                stats['avg_speed'] = self._parse_numeric_value(total_data.get('AverageSpeed', 0)) or 0
                stats['overspeed_count'] = int(total_data.get('OverspeedCount', 0))
                stats['park_count'] = int(total_data.get('ParkCount', 0))
                stats['motohours'] = self._time_str_to_hours(total_data.get('Engine1Motohours', '00:00:00'))
                stats['move_duration'] = self._time_str_to_hours(total_data.get('MoveDuration', '00:00:00'))
                stats['park_duration'] = self._time_str_to_hours(total_data.get('ParkDuration', '00:00:00'))

        # Округляем
        for key in ['total_distance', 'total_fuel', 'max_speed', 'avg_speed', 'motohours', 'move_duration',
                    'park_duration']:
            stats[key] = round(stats[key], 2)

        return stats

    def _create_vehicle_summary(self, trips_only_stats: Dict, trip_items_stats: Dict) -> Dict:
        """Создаем сводку по ТС"""
        return {
            'distance': trips_only_stats.get('total_distance', 0),
            'fuel': trips_only_stats.get('total_fuel', 0),
            'max_speed': trips_only_stats.get('max_speed', 0),
            'avg_speed': trips_only_stats.get('avg_speed', 0),
            'motohours': trips_only_stats.get('motohours', 0),
            'move_duration': trips_only_stats.get('move_duration', 0),
            'park_duration': trips_only_stats.get('park_duration', 0),
            'park_count': trips_only_stats.get('park_count', 0),
            'overspeed_count': trips_only_stats.get('overspeed_count', 0),
            'stage_count': trip_items_stats.get('stage_count', 0),
            'trip_count': trips_only_stats.get('trip_count', 0)
        }

    def _create_overall_summary(self, vehicles_data: Dict) -> Dict:
        """Создаем общую сводку"""
        summary = {
            'total_vehicles': len(vehicles_data),
            'total_distance': 0.0,
            'total_fuel': 0.0,
            'total_motohours': 0.0,
            'total_trips': 0,
            'total_stages': 0,
            'avg_speed': 0.0,
            'avg_max_speed': 0.0,
            'avg_rating': 0.0
        }

        total_speed = 0
        total_max_speed = 0
        total_rating = 0
        vehicles_with_data = 0

        for vehicle_id, vehicle_data in vehicles_data.items():
            vehicle_summary = vehicle_data.get('summary', {})
            trip_items_stats = vehicle_data.get('trip_items_stats', {})

            summary['total_distance'] += vehicle_summary.get('distance', 0)
            summary['total_fuel'] += vehicle_summary.get('fuel', 0)
            summary['total_motohours'] += vehicle_summary.get('motohours', 0)
            summary['total_trips'] += vehicle_summary.get('trip_count', 0)
            summary['total_stages'] += trip_items_stats.get('stage_count', 0)

            avg_speed = vehicle_summary.get('avg_speed', 0)
            max_speed = vehicle_summary.get('max_speed', 0)

            if avg_speed > 0:
                total_speed += avg_speed
                total_max_speed += max_speed
                vehicles_with_data += 1

        if vehicles_with_data > 0:
            summary['avg_speed'] = round(total_speed / vehicles_with_data, 2)
            summary['avg_max_speed'] = round(total_max_speed / vehicles_with_data, 2)

        # Округляем значения
        for key in ['total_distance', 'total_fuel', 'total_motohours']:
            summary[key] = round(summary[key], 2)

        return summary

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

    def _parse_numeric_value(self, value):
        """Парсинг числового значения"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                # Убираем запятые, заменяем на точки, удаляем пробелы
                clean_value = value.replace(',', '.').strip()
                if clean_value == '':
                    return None
                return float(clean_value)
            except:
                return None

        return None


class AutoGraphDeviceService:
    """Сервис для работы с устройствами AutoGRAPH"""

    BASE_URL = "https://web.tk-ekat.ru/ServiceJSON"

    def __init__(self, token=None):
        self.token = token
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'DeviceService/1.0'
        })

    def get_devices(self, schema_id: str) -> List[Dict]:
        """Получение списка устройств"""
        try:
            if not self.token or not schema_id:
                logger.error("Нет токена или ID схемя")
                return []

            # Запрос устройств через EnumDevices
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

            # Обработка ответа
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