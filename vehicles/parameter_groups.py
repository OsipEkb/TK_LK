"""
Группы параметров для анализа
"""

PARAMETER_GROUPS = {
    'speed_safety': {
        'name': 'Скорость и безопасность',
        'icon': 'fa-tachometer-alt',
        'color': '#e74c3c',
        'description': 'Показатели скорости и безопасности вождения',
        'chart_types': ['line', 'bar', 'radar'],
        'parameters': [
            'MaxSpeed', 'AverageSpeed', 'SpeedLimitMax', 'OverspeedCount',
            'DQRating', 'DQPoints', 'DQOverspeedPoints', 'DQExcessAccelPoints'
        ]
    },
    'engine_fuel': {
        'name': 'Двигатель и топливо',
        'icon': 'fa-gas-pump',
        'color': '#2ecc71',
        'description': 'Работа двигателя и расход топлива',
        'chart_types': ['line', 'bar', 'area'],
        'parameters': [
            'Engine1Motohours', 'Engine1FuelConsum', 'Engine1FuelConsumMPer100km',
            'Engine1FuelConsumM', 'Engine1FuelConsumP', 'Engine1MHOnParks'
        ]
    },
    'trip_info': {
        'name': 'Информация о поездках',
        'icon': 'fa-route',
        'color': '#3498db',
        'description': 'Основные показатели поездок',
        'chart_types': ['line', 'bar', 'pie'],
        'parameters': [
            'TotalDistance', 'TotalDuration', 'MoveDuration', 'ParkDuration',
            'ParkCount', 'FirstLocation', 'LastLocation'
        ]
    },
    'vehicle_stats': {
        'name': 'Статистика ТС',
        'icon': 'fa-chart-bar',
        'color': '#9b59b6',
        'description': 'Общая статистика транспортных средств',
        'chart_types': ['bar', 'pie', 'doughnut'],
        'parameters': [
            'TankMainFuelUpCount', 'TankMainFuelDnCount', 'TankMainFuelUpVol',
            'TankMainFuelDnVol', 'TankMainFuelLevel'
        ]
    }
}


class ParameterUtils:
    """Утилиты для работы с параметрами"""

    @staticmethod
    def get_parameter_display_name(param_name: str) -> str:
        """Получить отображаемое имя параметра"""
        display_names = {
            'MaxSpeed': 'Максимальная скорость',
            'AverageSpeed': 'Средняя скорость',
            'SpeedLimitMax': 'Максимальное ограничение',
            'OverspeedCount': 'Превышения скорости',
            'DQRating': 'Рейтинг вождения',
            'DQPoints': 'Баллы вождения',
            'DQOverspeedPoints': 'Баллы за превышения',
            'DQExcessAccelPoints': 'Баллы за ускорения',
            'Engine1Motohours': 'Моточасы',
            'Engine1FuelConsum': 'Расход топлива',
            'Engine1FuelConsumMPer100km': 'Расход л/100км',
            'Engine1FuelConsumM': 'Расход (м)',
            'Engine1FuelConsumP': 'Расход (п)',
            'Engine1MHOnParks': 'Моточасы на стоянке',
            'TotalDistance': 'Общий пробег',
            'TotalDuration': 'Общее время',
            'MoveDuration': 'Время движения',
            'ParkDuration': 'Время стоянки',
            'ParkCount': 'Количество стоянок',
            'FirstLocation': 'Начальная точка',
            'LastLocation': 'Конечная точка',
            'TankMainFuelUpCount': 'Заправки',
            'TankMainFuelDnCount': 'Сливы',
            'TankMainFuelUpVol': 'Объем заправок',
            'TankMainFuelDnVol': 'Объем сливов',
            'TankMainFuelLevel': 'Уровень топлива'
        }
        return display_names.get(param_name, param_name)

    @staticmethod
    def get_parameter_unit(param_name: str) -> str:
        """Получить единицу измерения параметра"""
        units = {
            'MaxSpeed': 'км/ч',
            'AverageSpeed': 'км/ч',
            'SpeedLimitMax': 'км/ч',
            'OverspeedCount': 'раз',
            'DQRating': '%',
            'DQPoints': 'баллы',
            'DQOverspeedPoints': 'баллы',
            'DQExcessAccelPoints': 'баллы',
            'Engine1Motohours': 'ч',
            'Engine1FuelConsum': 'л',
            'Engine1FuelConsumMPer100km': 'л/100км',
            'Engine1FuelConsumM': 'л',
            'Engine1FuelConsumP': 'л',
            'Engine1MHOnParks': 'ч',
            'TotalDistance': 'км',
            'TotalDuration': 'ч',
            'MoveDuration': 'ч',
            'ParkDuration': 'ч',
            'ParkCount': 'раз',
            'TankMainFuelUpCount': 'раз',
            'TankMainFuelDnCount': 'раз',
            'TankMainFuelUpVol': 'л',
            'TankMainFuelDnVol': 'л',
            'TankMainFuelLevel': '%'
        }
        return units.get(param_name, '')

    @staticmethod
    def get_parameter_type(param_name: str) -> str:
        """Получить тип параметра"""
        if param_name in ['MaxSpeed', 'AverageSpeed', 'SpeedLimitMax']:
            return 'speed'
        elif 'Fuel' in param_name:
            return 'fuel'
        elif 'Distance' in param_name:
            return 'distance'
        elif 'Duration' in param_name:
            return 'time'
        elif 'Rating' in param_name or 'Points' in param_name:
            return 'score'
        elif 'Count' in param_name:
            return 'count'
        elif 'Location' in param_name:
            return 'location'
        else:
            return 'other'


def get_parameter_group(param_name: str):
    """Получить группу параметра"""
    for group_id, group_data in PARAMETER_GROUPS.items():
        if param_name in group_data['parameters']:
            return {
                'id': group_id,
                'name': group_data['name'],
                'icon': group_data['icon'],
                'color': group_data['color']
            }
    return None


def get_all_parameters():
    """Получить все параметры"""
    all_params = {}
    for group_id, group_data in PARAMETER_GROUPS.items():
        for param in group_data['parameters']:
            all_params[param] = {
                'display_name': ParameterUtils.get_parameter_display_name(param),
                'unit': ParameterUtils.get_parameter_unit(param),
                'type': ParameterUtils.get_parameter_type(param),
                'group': group_id
            }
    return all_params