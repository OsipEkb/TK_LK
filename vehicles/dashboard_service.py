# vehicles/dashboard_service.py
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DashboardDataService:
    """Сервис для данных дашбордов на основе работающих методов"""

    def __init__(self, autograph_service):
        self.autograph_service = autograph_service

    def get_fuel_metrics_dashboard(self, schema_id: str, vehicle_ids: List[str], days: int = 1) -> Dict:
        """Дашборд 1: Основные метрики топлива"""
        try:
            # Устанавливаем период
            end_date = datetime.now() - timedelta(days=1)  # Вчера
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')

            dashboard_data = {
                'period': f"{start_date.strftime('%d.%m.%Y')}",
                'total_metrics': {},
                'vehicle_metrics': {},
                'last_update': datetime.now().isoformat()
            }

            total_fuel_consumption = 0
            total_mileage = 0
            total_engine_hours = "00:00:00"
            vehicle_count = 0

            for vehicle_id in vehicle_ids:
                trips_data = self.autograph_service.get_trips_total(schema_id, vehicle_id, start_date_str, end_date_str)

                if trips_data and vehicle_id in trips_data:
                    vehicle_data = trips_data[vehicle_id]

                    if 'Total' in vehicle_data and vehicle_data['Total']:
                        total = vehicle_data['Total']

                        # Основные метрики
                        fuel_consumption = total.get('Engine1FuelConsum', 0)
                        mileage = total.get('TotalDistance', 0)
                        engine_hours = total.get('Engine1Motohours', '00:00:00')
                        move_duration = total.get('MoveDuration', '00:00:00')
                        park_duration = total.get('ParkDuration', '00:00:00')
                        max_speed = total.get('MaxSpeed', 0)
                        refuel_count = total.get('TankMainFuelUpCount', 0)
                        refuel_volume = total.get('TankMainFuelUpVol Diff', 0)

                        # Суммируем для общих метрик
                        total_fuel_consumption += fuel_consumption
                        total_mileage += mileage
                        vehicle_count += 1

                        # Данные по каждому ТС
                        dashboard_data['vehicle_metrics'][vehicle_id] = {
                            'fuel_consumption': fuel_consumption,
                            'mileage': mileage,
                            'engine_hours': engine_hours,
                            'move_duration': move_duration,
                            'park_duration': park_duration,
                            'max_speed': max_speed,
                            'refuel_count': refuel_count,
                            'refuel_volume': refuel_volume
                        }

            # Общие метрики
            dashboard_data['total_metrics'] = {
                'total_fuel_consumption': total_fuel_consumption,
                'total_mileage': total_mileage,
                'avg_fuel_consumption': total_fuel_consumption / vehicle_count if vehicle_count else 0,
                'vehicle_count': vehicle_count,
                'date': start_date.strftime('%d.%m.%Y')
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Error in fuel metrics dashboard: {e}")
            return {}

    def get_fuel_analytics_dashboard(self, schema_id: str, vehicle_ids: List[str], days: int = 7) -> Dict:
        """Дашборд 2: Аналитика топлива"""
        try:
            analytics = {
                'period_days': days,
                'refueling_events': [],
                'fuel_consumption_trend': {},
                'alerts': [],
                'last_update': datetime.now().isoformat()
            }

            # Анализируем за несколько дней
            for day_offset in range(days):
                date = datetime.now() - timedelta(days=day_offset + 1)
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                start_date_str = start_date.strftime('%Y%m%d')
                end_date_str = date.strftime('%Y%m%d')

                day_data = {
                    'date': date.strftime('%d.%m.%Y'),
                    'total_fuel': 0,
                    'refuel_events': 0,
                    'vehicle_count': 0
                }

                for vehicle_id in vehicle_ids:
                    trips_data = self.autograph_service.get_trips_total(schema_id, vehicle_id, start_date_str,
                                                                        end_date_str)

                    if trips_data and vehicle_id in trips_data:
                        vehicle_data = trips_data[vehicle_id]

                        if 'Total' in vehicle_data and vehicle_data['Total']:
                            total = vehicle_data['Total']

                            fuel_consumption = total.get('Engine1FuelConsum', 0)
                            refuel_count = total.get('TankMainFuelUpCount', 0)
                            refuel_volume = total.get('TankMainFuelUpVol Diff', 0)

                            day_data['total_fuel'] += fuel_consumption
                            day_data['refuel_events'] += refuel_count
                            day_data['vehicle_count'] += 1

                            # Записываем события заправок
                            if refuel_count > 0:
                                analytics['refueling_events'].append({
                                    'date': date.strftime('%d.%m.%Y'),
                                    'vehicle_id': vehicle_id,
                                    'volume': refuel_volume,
                                    'count': refuel_count
                                })

                analytics['fuel_consumption_trend'][date.strftime('%d.%m.%Y')] = day_data

            return analytics

        except Exception as e:
            logger.error(f"Error in fuel analytics dashboard: {e}")
            return {}

    def get_technical_dashboard(self, schema_id: str, vehicle_ids: List[str]) -> Dict:
        """Дашборд 3: Технический мониторинг"""
        try:
            technical_data = {
                'online_status': {},
                'connection_issues': [],
                'sensor_alerts': [],
                'last_update': datetime.now().isoformat()
            }

            # Получаем онлайн данные
            online_data = self.autograph_service.get_online_info(schema_id, vehicle_ids)

            for vehicle_id in vehicle_ids:
                online_info = online_data.get(vehicle_id, {})

                # Статус онлайн
                is_online = bool(online_info)
                last_data_time = online_info.get('DT')

                technical_data['online_status'][vehicle_id] = {
                    'is_online': is_online,
                    'last_data': last_data_time,
                    'hours_offline': self._calculate_offline_hours(last_data_time) if not is_online else 0
                }

                # Проверяем проблемы
                if not is_online or self._is_data_old(last_data_time):
                    technical_data['connection_issues'].append({
                        'vehicle_id': vehicle_id,
                        'issue': 'offline' if not is_online else 'data_old',
                        'last_data': last_data_time
                    })

            return technical_data

        except Exception as e:
            logger.error(f"Error in technical dashboard: {e}")
            return {}

    def _calculate_offline_hours(self, last_data_time: str) -> float:
        """Вычисление времени оффлайн"""
        try:
            if not last_data_time:
                return 24.0

            last_dt = datetime.fromisoformat(last_data_time.replace('Z', '+00:00'))
            now = datetime.now().replace(tzinfo=last_dt.tzinfo)
            delta = now - last_dt
            return delta.total_seconds() / 3600
        except:
            return 24.0

    def _is_data_old(self, last_data_time: str, threshold_hours: int = 1) -> bool:
        """Проверка что данные устарели"""
        offline_hours = self._calculate_offline_hours(last_data_time)
        return offline_hours > threshold_hours