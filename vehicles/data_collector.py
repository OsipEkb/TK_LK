# vehicles/data_collector.py
import logging
from datetime import datetime, timedelta
from .services import AutoGraphDataCollector

logger = logging.getLogger(__name__)


class DataCollectionManager:
    """Менеджер для управления сбором данных из AutoGRAPH"""

    def __init__(self):
        self.collector = AutoGraphDataCollector()
        self.collection_history = []

    def run_comprehensive_collection(self, schema_id, days_back=7):
        """Запуск комплексного сбора данных"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            logger.info(f"🔄 Starting comprehensive data collection for {days_back} days")

            data = self.collector.collect_all_data(
                schema_id=schema_id,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            # Сохраняем данные
            filename = self.collector.save_collected_data()

            # Записываем в историю
            collection_record = {
                'timestamp': datetime.now().isoformat(),
                'schema_id': schema_id,
                'period': f"{start_date} to {end_date}",
                'data_file': filename,
                'data_keys': list(data.keys()) if data else []
            }
            self.collection_history.append(collection_record)

            logger.info(f"✅ Comprehensive collection completed: {len(data.keys())} data types collected")
            return data

        except Exception as e:
            logger.error(f"❌ Comprehensive collection failed: {e}")
            return None

    def get_collection_summary(self):
        """Получение сводки по собранным данным"""
        if not self.collector.collected_data:
            return {"status": "no_data", "message": "No data collected yet"}

        summary = {
            "status": "success",
            "total_data_types": len(self.collector.collected_data),
            "data_types": list(self.collector.collected_data.keys()),
            "collection_history": self.collection_history
        }

        # Добавляем статистику по каждому типу данных
        for key, data in self.collector.collected_data.items():
            if isinstance(data, list):
                summary[f"{key}_count"] = len(data)
            elif isinstance(data, dict):
                summary[f"{key}_keys"] = list(data.keys())
                summary[f"{key}_count"] = len(data)
            else:
                summary[f"{key}_type"] = type(data).__name__

        return summary

    def get_specific_data(self, data_type, schema_id, **kwargs):
        """Получение конкретного типа данных"""
        try:
            if data_type == 'vehicles':
                return self.collector.service.get_vehicles(schema_id)
            elif data_type == 'drivers':
                return self.collector.service.get_drivers(schema_id)
            elif data_type == 'geofences':
                return self.collector.service.get_geofences(schema_id)
            elif data_type == 'online_info':
                device_ids = kwargs.get('device_ids')
                return self.collector.service.get_online_info(schema_id, device_ids)
            elif data_type == 'track_data':
                device_ids = kwargs.get('device_ids')
                start_date = kwargs.get('start_date')
                end_date = kwargs.get('end_date')
                start_fmt = self.collector.service.format_date_for_api(start_date + "T00:00")
                end_fmt = self.collector.service.format_date_for_api(end_date + "T23:59")
                return self.collector.service.get_track_data(schema_id, device_ids, start_fmt, end_fmt)
            # Добавьте другие типы данных по необходимости
            else:
                logger.error(f"❌ Unknown data type: {data_type}")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting {data_type}: {e}")
            return None


# Глобальный экземпляр менеджера
data_manager = DataCollectionManager()