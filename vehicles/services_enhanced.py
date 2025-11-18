# vehicles/services_enhanced.py
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .services import AutoGraphService

logger = logging.getLogger(__name__)


@dataclass
class VehicleSummary:
    """Датакласс для сводной информации о ТС"""
    vehicle_id: str
    name: str
    license_plate: str
    total_distance: float
    total_fuel: float
    avg_speed: float
    max_speed: float
    engine_hours: str
    last_update: str
    status: str
    location: str


@dataclass
class TripData:
    """Датакласс для данных о рейсе"""
    start_time: str
    end_time: str
    distance: float
    duration: str
    fuel_consumption: float
    max_speed: float
    start_location: str
    end_location: str


@dataclass
class WorkAnalysis:
    """Датакласс для анализа работы"""
    engine_work_without_movement: int  # в секундах
    engine_work_in_motion: int  # в секундах
    parking_engine_off: int  # в секундах
    no_data: int  # в секундах
    total_period: int  # в секундах


class EnhancedAutoGraphService(AutoGraphService):
    """Улучшенный сервис с дополнительными возможностями"""

    def __init__(self):
        super().__init__()
        self.cache = {}
        self.cache_timeout = 300  # 5 минут

    def get_online_info(self, schema_id: str, vehicle_id: str) -> Dict:
        """Получение онлайн информации по конкретному ТС"""
        try:
            online_data = self.get_online_info_all(schema_id)
            return {vehicle_id: online_data.get(vehicle_id, {})} if online_data else {}
        except Exception as e:
            logger.error(f"❌ Error getting online info for {vehicle_id}: {e}")
            return {}

    def extract_license_plate_enhanced(self, vehicle_data: Dict) -> str:
        """Улучшенное извлечение госномера"""
        try:
            # Пробуем разные варианты полей
            possible_fields = ['VRN', 'LicensePlate', 'Госномер', 'RegNumber', 'VehicleRegNumber']

            # Прямые поля
            for field in possible_fields:
                value = vehicle_data.get(field)
                if value and str(value).strip() and str(value).strip().lower() != 'unknown':
                    return str(value).strip()

            # Поля в Properties
            properties = vehicle_data.get('Properties', [])
            for prop in properties:
                if prop.get('Name') in possible_fields:
                    value = prop.get('Value', '')
                    if value and str(value).strip() and str(value).strip().lower() != 'unknown':
                        return str(value).strip()

            # Из имени
            name = vehicle_data.get('Name', '')
            if name:
                return name

            return 'Unknown'

        except Exception as e:
            logger.error(f"❌ Error extracting license plate: {e}")
            return vehicle_data.get('Name', 'Unknown')

    def get_comprehensive_vehicle_data(self, schema_id: str, vehicle_id: str,
                                       start_date: str, end_date: str) -> Dict:
        """Получение комплексных данных по ТС для аналитики"""
        try:
            start_fmt = self.format_date_for_api(start_date, is_start=True)
            end_fmt = self.format_date_for_api(end_date, is_start=False)

            comprehensive_data = {
                'basic_info': {},
                'trips_data': [],
                'track_data': [],
                'online_data': {},
                'fuel_analysis': {},
                'work_analysis': {},
                'summary_stats': {}
            }

            # 1. Базовая информация
            vehicles_info = self.get_vehicles(schema_id)
            if vehicles_info and 'Items' in vehicles_info:
                for vehicle in vehicles_info['Items']:
                    if str(vehicle.get('ID')) == vehicle_id:
                        comprehensive_data['basic_info'] = {
                            'id': vehicle_id,
                            'name': vehicle.get('Name'),
                            'license_plate': self.extract_license_plate_enhanced(vehicle),
                            'serial': vehicle.get('Serial'),
                            'properties': vehicle.get('Properties', [])
                        }
                        break

            # 2. Данные рейсов
            trips_total = self.get_trips_total(schema_id, vehicle_id, start_fmt, end_fmt)
            if trips_total and vehicle_id in trips_total:
                vehicle_trips = trips_total[vehicle_id]
                comprehensive_data['trips_data'] = self._process_trips_for_analytics(vehicle_trips)

            # 3. Данные трека
            track_data = self.get_track_data(schema_id, vehicle_id, start_fmt, end_fmt)
            if track_data and vehicle_id in track_data:
                comprehensive_data['track_data'] = self._process_track_for_analytics(track_data[vehicle_id])

            # 4. Онлайн данные
            online_info = self.get_online_info(schema_id, vehicle_id)
            if online_info and vehicle_id in online_info:
                comprehensive_data['online_data'] = online_info[vehicle_id]

            # 5. Анализ топлива
            comprehensive_data['fuel_analysis'] = self.get_fuel_consumption_analysis(
                schema_id, vehicle_id, start_date, end_date
            )

            # 6. Анализ работы
            work_analysis = self.get_work_analysis(schema_id, vehicle_id, start_date, end_date)
            comprehensive_data['work_analysis'] = self._format_work_analysis(work_analysis)

            # 7. Сводная статистика
            comprehensive_data['summary_stats'] = self._calculate_summary_stats(comprehensive_data)

            return comprehensive_data

        except Exception as e:
            logger.error(f"❌ Error getting comprehensive data for {vehicle_id}: {e}")
            return {}

    def get_work_analysis(self, schema_id: str, vehicle_id: str,
                          start_date: str, end_date: str) -> WorkAnalysis:
        """Анализ работы ТС за период с улучшенной логикой"""
        try:
            start_fmt = self.format_date_for_api(start_date, is_start=True)
            end_fmt = self.format_date_for_api(end_date, is_start=False)

            logger.info(f"🔍 Анализ работы для {vehicle_id} с {start_fmt} по {end_fmt}")

            # Получаем данные трека
            track_data = self.get_track_data(schema_id, vehicle_id, start_fmt, end_fmt)

            if not track_data or vehicle_id not in track_data:
                logger.info("❌ Нет данных трека")
                return self._create_empty_work_analysis(start_date, end_date)

            track_points = track_data[vehicle_id]
            logger.info(f"📍 Получено точек трека: {len(track_points) if track_points else 0}")

            # Анализируем работу
            analysis = self._analyze_work_from_track(track_points, start_date, end_date)

            logger.info(f"📊 Результат анализа: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"❌ Ошибка в work analysis: {e}")
            return self._create_empty_work_analysis(start_date, end_date)

    def _analyze_work_from_track(self, track_points: List[Dict], start_date: str, end_date: str) -> WorkAnalysis:
        """Анализ работы из данных трека с улучшенной логикой"""
        try:
            # Сортируем точки по времени
            valid_points = [p for p in track_points if p.get('_SD')]
            if not valid_points:
                return self._create_empty_work_analysis(start_date, end_date)

            sorted_points = sorted(valid_points, key=lambda x: x.get('_SD', ''))

            # Рассчитываем общее время периода
            start_dt = self._parse_timestamp(start_date)
            end_dt = self._parse_timestamp(end_date)

            if not start_dt or not end_dt:
                return self._create_empty_work_analysis(start_date, end_date)

            total_period_seconds = int((end_dt - start_dt).total_seconds())

            # Упрощенный анализ на основе статистики точек
            motion_count = sum(1 for p in sorted_points if p.get('Motion') == 2)
            ignition_count = sum(1 for p in sorted_points if p.get('DIgnition') is True)
            total_points = len(sorted_points)

            if total_points == 0:
                return self._create_empty_work_analysis(start_date, end_date)

            motion_ratio = motion_count / total_points
            ignition_ratio = ignition_count / total_points

            # Эвристическое распределение времени
            engine_work_in_motion = int(total_period_seconds * motion_ratio * 0.8)
            engine_work_without_movement = int(total_period_seconds * (ignition_ratio - motion_ratio) * 0.7)
            parking_engine_off = int(total_period_seconds * (1 - ignition_ratio) * 0.6)
            no_data = total_period_seconds - (engine_work_in_motion + engine_work_without_movement + parking_engine_off)

            # Корректировка, чтобы сумма была равна total_period_seconds
            no_data = max(0, no_data)

            return WorkAnalysis(
                engine_work_without_movement=engine_work_without_movement,
                engine_work_in_motion=engine_work_in_motion,
                parking_engine_off=parking_engine_off,
                no_data=no_data,
                total_period=total_period_seconds
            )

        except Exception as e:
            logger.error(f"❌ Ошибка анализа работы из трека: {e}")
            return self._create_empty_work_analysis(start_date, end_date)

    def _create_empty_work_analysis(self, start_date: str, end_date: str) -> WorkAnalysis:
        """Создание пустого анализа работы"""
        try:
            start_dt = self._parse_timestamp(start_date)
            end_dt = self._parse_timestamp(end_date)

            if start_dt and end_dt:
                total_seconds = int((end_dt - start_dt).total_seconds())
            else:
                total_seconds = 86400  # 24 часа

            return WorkAnalysis(
                engine_work_without_movement=0,
                engine_work_in_motion=0,
                parking_engine_off=0,
                no_data=total_seconds,
                total_period=total_seconds
            )
        except:
            return WorkAnalysis(
                engine_work_without_movement=0,
                engine_work_in_motion=0,
                parking_engine_off=0,
                no_data=86400,
                total_period=86400
            )

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Парсинг временной метки"""
        try:
            if not timestamp_str:
                return None

            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S',
                '%Y%m%d-%H%M%S',
                '%Y-%m-%d'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue

            return None
        except Exception as e:
            logger.error(f"❌ Error parsing timestamp {timestamp_str}: {e}")
            return None

    def _format_work_analysis(self, work_analysis: WorkAnalysis) -> Dict:
        """Форматирование анализа работы для фронтенда"""
        total = work_analysis.total_period

        return {
            'engine_work_without_movement': {
                'seconds': work_analysis.engine_work_without_movement,
                'formatted': self._format_seconds_to_time(work_analysis.engine_work_without_movement),
                'percentage': round((work_analysis.engine_work_without_movement / total) * 100, 1) if total > 0 else 0
            },
            'engine_work_in_motion': {
                'seconds': work_analysis.engine_work_in_motion,
                'formatted': self._format_seconds_to_time(work_analysis.engine_work_in_motion),
                'percentage': round((work_analysis.engine_work_in_motion / total) * 100, 1) if total > 0 else 0
            },
            'parking_engine_off': {
                'seconds': work_analysis.parking_engine_off,
                'formatted': self._format_seconds_to_time(work_analysis.parking_engine_off),
                'percentage': round((work_analysis.parking_engine_off / total) * 100, 1) if total > 0 else 0
            },
            'no_data': {
                'seconds': work_analysis.no_data,
                'formatted': self._format_seconds_to_time(work_analysis.no_data),
                'percentage': round((work_analysis.no_data / total) * 100, 1) if total > 0 else 0
            },
            'total_period': {
                'seconds': total,
                'formatted': self._format_seconds_to_time(total)
            }
        }

    def _format_seconds_to_time(self, total_seconds: int) -> str:
        """Форматирование секунд в читаемый формат времени"""
        try:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)

            if hours > 0:
                return f"{hours} час. {minutes} мин."
            else:
                return f"{minutes} мин."
        except:
            return "0 мин."

    def _process_trips_for_analytics(self, trips_data):
        """Обработка данных рейсов для аналитики"""
        processed_trips = []

        for trip in trips_data.get('Trips', []):
            total = trip.get('Total', {})

            processed_trip = {
                'start_time': trip.get('SD'),
                'end_time': trip.get('ED'),
                'distance': total.get('TotalDistance', 0),
                'duration': total.get('TotalDuration', '00:00:00'),
                'fuel_consumption': total.get('Engine1FuelConsum', 0),
                'max_speed': total.get('MaxSpeed', 0),
                'avg_speed': total.get('AverageSpeed', 0),
                'engine_hours': total.get('Engine1Motohours', '00:00:00'),
                'parking_count': total.get('ParkCount', 0),
                'overspeed_count': total.get('OverspeedCount', 0),
                'start_location': total.get('FirstLocation', ''),
                'end_location': total.get('LastLocation', ''),
                'fuel_efficiency': self._calculate_fuel_efficiency(
                    total.get('Engine1FuelConsum', 0),
                    total.get('TotalDistance', 0)
                )
            }

            processed_trips.append(processed_trip)

        return processed_trips

    def _process_track_for_analytics(self, track_points):
        """Обработка данных трека для аналитики"""
        if not track_points:
            return []

        processed_track = []

        for point in track_points:
            processed_point = {
                'timestamp': point.get('_SD'),
                'coordinates': {
                    'lat': point.get('Lat'),
                    'lng': point.get('Lng')
                },
                'speed': point.get('Speed', 0),
                'fuel_level': point.get('TankMainFuelLevel', 0),
                'engine_rpm': point.get('Engine1RPM', 0),
                'voltage': point.get('Power', 0),
                'mileage': point.get('Mileage', 0),
                'satellites': point.get('Satellites', 0),
                'hdop': point.get('HDOP', 0),
                'ignition': point.get('DIgnition', False),
                'movement': point.get('Motion', 1)
            }

            processed_track.append(processed_point)

        return processed_track

    def _calculate_fuel_efficiency(self, fuel, distance):
        """Расчет топливной эффективности"""
        return (fuel / distance * 100) if distance > 0 else 0

    def _calculate_summary_stats(self, comprehensive_data):
        """Расчет сводной статистики"""
        trips = comprehensive_data.get('trips_data', [])

        if not trips:
            return {}

        total_distance = sum(trip.get('distance', 0) for trip in trips)
        total_fuel = sum(trip.get('fuel_consumption', 0) for trip in trips)
        total_duration = sum(self._parse_duration(trip.get('duration', '00:00:00')) for trip in trips)

        return {
            'total_distance': round(total_distance, 2),
            'total_fuel_consumption': round(total_fuel, 2),
            'total_engine_hours': self._format_duration(total_duration),
            'avg_fuel_efficiency': round((total_fuel / total_distance * 100), 2) if total_distance > 0 else 0,
            'trips_count': len(trips),
            'avg_trip_distance': round(total_distance / len(trips), 2) if trips else 0,
            'avg_trip_duration': self._format_duration(total_duration / len(trips)) if trips else '00:00:00'
        }

    def _parse_duration(self, duration_str: str) -> int:
        """Парсинг длительности в секунды"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            return 0
        except:
            return 0

    def _format_duration(self, total_seconds):
        """Форматирование секунд в строку HH:MM:SS"""
        try:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"

    def get_fuel_consumption_analysis(self, schema_id: str, vehicle_id: str,
                                      start_date: str, end_date: str) -> Dict:
        """Анализ расхода топлива"""
        try:
            trips = self._process_trips_for_analytics(
                self.get_trips_total(schema_id, vehicle_id,
                                     self.format_date_for_api(start_date, True),
                                     self.format_date_for_api(end_date, False)).get(vehicle_id, {})
            )

            if not trips:
                return {}

            total_fuel = sum(trip.get('fuel_consumption', 0) for trip in trips)
            total_distance = sum(trip.get('distance', 0) for trip in trips)
            total_duration = sum(self._parse_duration(trip.get('duration', '00:00:00')) for trip in trips)

            # Расчет эффективности
            fuel_efficiency = (total_fuel / total_distance * 100) if total_distance > 0 else 0
            fuel_per_hour = (total_fuel / (total_duration / 3600)) if total_duration > 0 else 0

            return {
                'total_fuel_consumption': round(total_fuel, 2),
                'total_distance': round(total_distance, 2),
                'fuel_efficiency_100km': round(fuel_efficiency, 2),
                'fuel_consumption_per_hour': round(fuel_per_hour, 2),
                'average_trip_distance': round(total_distance / len(trips), 2) if trips else 0,
                'average_trip_fuel': round(total_fuel / len(trips), 2) if trips else 0,
                'trips_analyzed': len(trips)
            }

        except Exception as e:
            logger.error(f"❌ Error in fuel consumption analysis: {e}")
            return {}