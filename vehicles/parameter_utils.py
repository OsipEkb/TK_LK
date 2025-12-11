"""
Утилиты для работы с параметрами AutoGRAPH
"""


class ParameterTranslator:
    """Класс для перевода и группировки параметров"""

    PARAMETER_GROUPS = {
        'time_date': {
            'name': 'Время и дата',
            'icon': 'fa-clock',
            'color': '#3498db',
            'parameters': [
                {'api_name': 'DateTime First', 'display_name': 'Начало периода', 'unit': ''},
                {'api_name': 'DateTime Last', 'display_name': 'Конец периода', 'unit': ''},
                {'api_name': 'StartOfFirstReg', 'display_name': 'Начало первой регистрации', 'unit': ''},
                {'api_name': 'EndOfLastReg', 'display_name': 'Конец последней регистрации', 'unit': ''},
                {'api_name': 'StartOfFirstPark', 'display_name': 'Начало первой стоянки', 'unit': ''},
                {'api_name': 'EndOfLastPark', 'display_name': 'Конец последней стоянки', 'unit': ''},
                {'api_name': 'StartOfFirstMove', 'display_name': 'Начало первого движения', 'unit': ''},
                {'api_name': 'EndOfLastMove', 'display_name': 'Конец последнего движения', 'unit': ''},
                {'api_name': 'TotalDuration', 'display_name': 'Общее время', 'unit': 'ч'},
                {'api_name': 'MoveDuration', 'display_name': 'Время движения', 'unit': 'ч'},
                {'api_name': 'ParkDuration', 'display_name': 'Время стоянки', 'unit': 'ч'}
            ]
        },
        'location': {
            'name': 'Координаты',
            'icon': 'fa-map-marker-alt',
            'color': '#2ecc71',
            'parameters': [
                {'api_name': 'Longitude First', 'display_name': 'Начальная долгота', 'unit': '°'},
                {'api_name': 'Longitude Last', 'display_name': 'Конечная долгота', 'unit': '°'},
                {'api_name': 'Latitude First', 'display_name': 'Начальная широта', 'unit': '°'},
                {'api_name': 'Latitude Last', 'display_name': 'Конечная широта', 'unit': '°'},
                {'api_name': 'FirstLocation', 'display_name': 'Начальное местоположение', 'unit': ''},
                {'api_name': 'LastLocation', 'display_name': 'Конечное местоположение', 'unit': ''}
            ]
        },
        'speed_motion': {
            'name': 'Скорость и движение',
            'icon': 'fa-tachometer-alt',
            'color': '#e74c3c',
            'parameters': [
                {'api_name': 'TotalDistance', 'display_name': 'Общий пробег', 'unit': 'км'},
                {'api_name': 'SpeedLimitMax Last', 'display_name': 'Макс. ограничение скорости', 'unit': 'км/ч'},
                {'api_name': 'MaxSpeed', 'display_name': 'Максимальная скорость', 'unit': 'км/ч'},
                {'api_name': 'AverageSpeed', 'display_name': 'Средняя скорость', 'unit': 'км/ч'},
                {'api_name': 'OverspeedCount', 'display_name': 'Превышений скорости', 'unit': 'раз'},
                {'api_name': 'ParkCount', 'display_name': 'Количество стоянок', 'unit': 'раз'}
            ]
        },
        'fuel': {
            'name': 'Топливо',
            'icon': 'fa-gas-pump',
            'color': '#f39c12',
            'parameters': [
                {'api_name': 'Engine1FuelConsum', 'display_name': 'Расход топлива', 'unit': 'л'},
                {'api_name': 'Engine1FuelConsumP', 'display_name': 'Расход топлива (P)', 'unit': 'л'},
                {'api_name': 'Engine1FuelConsumPPerHour', 'display_name': 'Расход P в час', 'unit': 'л/ч'},
                {'api_name': 'Engine1FuelConsumPPerMH', 'display_name': 'Расход P на моточас', 'unit': 'л/МЧ'},
                {'api_name': 'Engine1FuelConsumM', 'display_name': 'Расход топлива (M)', 'unit': 'л'},
                {'api_name': 'Engine1FuelConsumMPer100km', 'display_name': 'Расход на 100 км', 'unit': 'л/100км'},
                {'api_name': 'Engine1FuelConsumMPerMH', 'display_name': 'Расход M на моточас', 'unit': 'л/МЧ'},
                {'api_name': 'Engine1FuelConsumDuringMH', 'display_name': 'Расход при работе', 'unit': 'л'},
                {'api_name': 'Engine1FuelConsumPDuringMH', 'display_name': 'Расход P при работе', 'unit': 'л'},
                {'api_name': 'Engine1FuelConsumMDuringMH', 'display_name': 'Расход M при работе', 'unit': 'л'},
                {'api_name': 'TankMainFuelLevel First', 'display_name': 'Топливо на начало', 'unit': 'л'},
                {'api_name': 'TankMainFuelLevel Last', 'display_name': 'Топливо на конец', 'unit': 'л'},
                {'api_name': 'TankMainFuelUpVol Diff', 'display_name': 'Заправки', 'unit': 'л'},
                {'api_name': 'TankMainFuelDnVol Diff', 'display_name': 'Сливы', 'unit': 'л'},
                {'api_name': 'TankMainFuelUpCount', 'display_name': 'Количество заправок', 'unit': 'раз'},
                {'api_name': 'TankMainFuelDnCount', 'display_name': 'Количество сливов', 'unit': 'раз'},
                {'api_name': 'TankMainFuelUpDnVol', 'display_name': 'Общий объем заправок/сливов', 'unit': 'л'}
            ]
        },
        'engine': {
            'name': 'Двигатель',
            'icon': 'fa-cogs',
            'color': '#9b59b6',
            'parameters': [
                {'api_name': 'Engine1Motohours', 'display_name': 'Моточасы', 'unit': 'ч'},
                {'api_name': 'Engine1MHOnParks', 'display_name': 'Моточасы на стоянке', 'unit': 'ч'},
                {'api_name': 'Engine1MHInMove', 'display_name': 'Моточасы в движении', 'unit': 'ч'}
            ]
        },
        'driving_quality': {
            'name': 'Качество вождения',
            'icon': 'fa-shield-alt',
            'color': '#1abc9c',
            'parameters': [
                {'api_name': 'DQRating', 'display_name': 'Рейтинг вождения', 'unit': '%'},
                {'api_name': 'DQOverspeedPoints Diff', 'display_name': 'Штрафы за превышение', 'unit': 'баллы'},
                {'api_name': 'DQExcessAccelPoints Diff', 'display_name': 'Штрафы за ускорение', 'unit': 'баллы'},
                {'api_name': 'DQExcessBrakePoints Diff', 'display_name': 'Штрафы за торможение', 'unit': 'баллы'},
                {'api_name': 'DQEmergencyBrakePoints Diff', 'display_name': 'Штрафы за экстр. торможение',
                 'unit': 'баллы'},
                {'api_name': 'DQExcessRightPoints Diff', 'display_name': 'Штрафы за правые повороты', 'unit': 'баллы'},
                {'api_name': 'DQExcessLeftPoints Diff', 'display_name': 'Штрафы за левые повороты', 'unit': 'баллы'},
                {'api_name': 'DQExcessBumpPoints Diff', 'display_name': 'Штрафы за тряску', 'unit': 'баллы'},
                {'api_name': 'DQPoints Diff', 'display_name': 'Всего штрафных баллов', 'unit': 'баллы'}
            ]
        }
    }

    TRANSLATION_MAP = {
        'DateTime First': 'Начало периода',
        'DateTime Last': 'Конец периода',
        'Longitude First': 'Начальная долгота',
        'Longitude Last': 'Конечная долгота',
        'Latitude First': 'Начальная широта',
        'Latitude Last': 'Конечная широта',
        'StartOfFirstReg': 'Начало первой регистрации',
        'EndOfLastReg': 'Конец последней регистрации',
        'TotalDuration': 'Общее время',
        'MoveDuration': 'Время движения',
        'ParkDuration': 'Время стоянки',
        'TotalDistance': 'Общий пробег',
        'StartOfFirstPark': 'Начало первой стоянки',
        'EndOfLastPark': 'Конец последней стоянки',
        'StartOfFirstMove': 'Начало первого движения',
        'EndOfLastMove': 'Конец последнего движения',
        'ParkCount': 'Количество стоянок',
        'SpeedLimitMax Last': 'Макс. ограничение скорости',
        'MaxSpeed': 'Максимальная скорость',
        'AverageSpeed': 'Средняя скорость',
        'OverspeedCount': 'Превышений скорости',
        'FirstLocation': 'Начальное местоположение',
        'LastLocation': 'Конечное местоположение',
        'DQOverspeedPoints Diff': 'Штрафы за превышение',
        'DQExcessAccelPoints Diff': 'Штрафы за ускорение',
        'DQExcessBrakePoints Diff': 'Штрафы за торможение',
        'DQEmergencyBrakePoints Diff': 'Штрафы за экстр. торможение',
        'DQExcessRightPoints Diff': 'Штрафы за правые повороты',
        'DQExcessLeftPoints Diff': 'Штрафы за левые повороты',
        'DQExcessBumpPoints Diff': 'Штрафы за тряску',
        'DQPoints Diff': 'Всего штрафных баллов',
        'DQRating': 'Рейтинг вождения',
        'Engine1Motohours': 'Моточасы',
        'Engine1MHOnParks': 'Моточасы на стоянке',
        'Engine1MHInMove': 'Моточасы в движении',
        'Engine1FuelConsum': 'Расход топлива',
        'Engine1FuelConsumP': 'Расход топлива (P)',
        'Engine1FuelConsumPPerHour': 'Расход P в час',
        'Engine1FuelConsumPPerMH': 'Расход P на моточас',
        'Engine1FuelConsumM': 'Расход топлива (M)',
        'Engine1FuelConsumMPer100km': 'Расход на 100 км',
        'Engine1FuelConsumMPerMH': 'Расход M на моточас',
        'Engine1FuelConsumDuringMH': 'Расход при работе',
        'Engine1FuelConsumPDuringMH': 'Расход P при работе',
        'Engine1FuelConsumMDuringMH': 'Расход M при работе',
        'TankMainFuelLevel First': 'Топливо на начало',
        'TankMainFuelLevel Last': 'Топливо на конец',
        'TankMainFuelUpVol Diff': 'Заправки',
        'TankMainFuelDnVol Diff': 'Сливы',
        'TankMainFuelUpCount': 'Количество заправок',
        'TankMainFuelDnCount': 'Количество сливов',
        'TankMainFuelUpDnVol': 'Общий объем заправок/сливов'
    }

    UNIT_MAP = {
        'DateTime First': '',
        'DateTime Last': '',
        'Longitude First': '°',
        'Longitude Last': '°',
        'Latitude First': '°',
        'Latitude Last': '°',
        'StartOfFirstReg': '',
        'EndOfLastReg': '',
        'TotalDuration': 'ч',
        'MoveDuration': 'ч',
        'ParkDuration': 'ч',
        'TotalDistance': 'км',
        'StartOfFirstPark': '',
        'EndOfLastPark': '',
        'StartOfFirstMove': '',
        'EndOfLastMove': '',
        'ParkCount': 'раз',
        'SpeedLimitMax Last': 'км/ч',
        'MaxSpeed': 'км/ч',
        'AverageSpeed': 'км/ч',
        'OverspeedCount': 'раз',
        'FirstLocation': '',
        'LastLocation': '',
        'DQOverspeedPoints Diff': 'баллы',
        'DQExcessAccelPoints Diff': 'баллы',
        'DQExcessBrakePoints Diff': 'баллы',
        'DQEmergencyBrakePoints Diff': 'баллы',
        'DQExcessRightPoints Diff': 'баллы',
        'DQExcessLeftPoints Diff': 'баллы',
        'DQExcessBumpPoints Diff': 'баллы',
        'DQPoints Diff': 'баллы',
        'DQRating': '%',
        'Engine1Motohours': 'ч',
        'Engine1MHOnParks': 'ч',
        'Engine1MHInMove': 'ч',
        'Engine1FuelConsum': 'л',
        'Engine1FuelConsumP': 'л',
        'Engine1FuelConsumPPerHour': 'л/ч',
        'Engine1FuelConsumPPerMH': 'л/МЧ',
        'Engine1FuelConsumM': 'л',
        'Engine1FuelConsumMPer100km': 'л/100км',
        'Engine1FuelConsumMPerMH': 'л/МЧ',
        'Engine1FuelConsumDuringMH': 'л',
        'Engine1FuelConsumPDuringMH': 'л',
        'Engine1FuelConsumMDuringMH': 'л',
        'TankMainFuelLevel First': 'л',
        'TankMainFuelLevel Last': 'л',
        'TankMainFuelUpVol Diff': 'л',
        'TankMainFuelDnVol Diff': 'л',
        'TankMainFuelUpCount': 'раз',
        'TankMainFuelDnCount': 'раз',
        'TankMainFuelUpDnVol': 'л'
    }

    @classmethod
    def get_parameter_groups(cls):
        """Получение всех групп параметров"""
        return cls.PARAMETER_GROUPS

    @classmethod
    def translate_parameter(cls, api_name):
        """Перевод одного параметра"""
        return cls.TRANSLATION_MAP.get(api_name, api_name)

    @classmethod
    def get_parameter_unit(cls, api_name):
        """Получение единицы измерения параметра"""
        return cls.UNIT_MAP.get(api_name, '')

    @classmethod
    def group_parameters(cls, api_parameters):
        """Группировка списка параметров API по категориям"""
        result = {}

        # Инициализируем все группы
        for group_id, group_data in cls.PARAMETER_GROUPS.items():
            result[group_id] = {
                'name': group_data['name'],
                'icon': group_data['icon'],
                'color': group_data['color'],
                'parameters': []
            }

        # Добавляем "Другие параметры" для нераспределенных
        result['other'] = {
            'name': 'Другие параметры',
            'icon': 'fa-ellipsis-h',
            'color': '#95a5a6',
            'parameters': []
        }

        # Распределяем параметры по группам
        for api_param in api_parameters:
            found = False

            # Ищем параметр в группах
            for group_id, group_data in cls.PARAMETER_GROUPS.items():
                for param_def in group_data['parameters']:
                    if param_def['api_name'] == api_param:
                        translated_name = cls.translate_parameter(api_param)
                        unit = cls.get_parameter_unit(api_param)

                        result[group_id]['parameters'].append({
                            'api_name': api_param,
                            'display_name': translated_name,
                            'unit': unit
                        })
                        found = True
                        break
                if found:
                    break

            # Если не нашли в группах, добавляем в "Другие"
            if not found:
                result['other']['parameters'].append({
                    'api_name': api_param,
                    'display_name': api_param,  # Без перевода
                    'unit': ''
                })

        # Удаляем пустые группы
        result = {k: v for k, v in result.items() if v['parameters']}

        return result

    @classmethod
    def get_parameter_info(cls, api_name):
        """Получение полной информации о параметре"""
        return {
            'api_name': api_name,
            'display_name': cls.translate_parameter(api_name),
            'unit': cls.get_parameter_unit(api_name)
        }