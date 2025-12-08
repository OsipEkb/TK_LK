from django.shortcuts import render, redirect
from django.http import JsonResponse
import logging
from datetime import datetime
from .services import AutoGraphService

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """Основной дашборд"""
    token = request.session.get('autograph_token')
    schema_id = request.session.get('autograph_schema_id')

    if not token or not schema_id:
        return redirect('users:login')

    return render(request, 'dashboard/dashboard.html', {
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'schema_name': request.session.get('autograph_schema_name', 'Неизвестно'),
        'username': request.session.get('autograph_username', 'Пользователь'),
    })


def dashboard_api_view(request):
    """API для получения данных дашборда"""
    token = request.session.get('autograph_token')
    schema_id = request.session.get('autograph_schema_id')

    if not token or not schema_id:
        return JsonResponse({'success': False, 'error': 'Требуется авторизация'}, status=401)

    try:
        service = AutoGraphService(token=token)

        # 1. Получаем все устройства
        devices = service.get_devices(schema_id)

        if not devices:
            return JsonResponse({
                'success': True,
                'data': {
                    'vehicles': [],
                    'total': 0,
                    'online': 0,
                    'warning': 0,
                    'offline': 0,
                }
            })

        # 2. Получаем онлайн данные для ВСЕХ устройств
        device_ids = [d['id'] for d in devices]
        online_data = service.get_online_data(schema_id, device_ids)

        # 3. Формируем данные для дашборда
        vehicles = []
        stats = {'total': 0, 'online': 0, 'warning': 0, 'offline': 0}

        for device in devices:
            device_id = device['id']
            online = online_data.get(device_id) if isinstance(online_data, dict) else None

            # Определяем статус
            status = 'offline'
            if online:
                # Проверяем скорость
                speed = 0
                if 'Speed' in online:
                    try:
                        speed = float(online['Speed'])
                    except:
                        pass

                if speed > 1:  # Если движется
                    status = 'online'
                else:  # Если стоит
                    status = 'warning'

            stats[status] += 1
            stats['total'] += 1

            # Скорость
            speed = 0
            if online and 'Speed' in online:
                try:
                    speed = float(online['Speed'])
                except:
                    pass

            # Топливо - используем существующий метод
            fuel_volume = 0
            if online:
                fuel_data = service.extract_fuel_data(online)
                fuel_volume = fuel_data.get('total_volume', 0)

            # Адрес
            address = online.get('Address', '') if online else ''

            # Время обновления
            last_update = ''
            if online:
                for field in ['DTLocal', 'DT', '_LastDataLocal']:
                    if field in online and online[field]:
                        last_update = online[field]
                        break

            vehicles.append({
                'id': device_id,
                'name': device['name'],
                'license_plate': device['reg_num'],
                'serial': device['serial'],
                'status': status,
                'speed': speed,
                'fuel_volume': fuel_volume,  # Объем топлива в литрах
                'address': address,
                'last_update': last_update,
            })

        return JsonResponse({
            'success': True,
            'data': {
                'vehicles': vehicles,
                'total': stats['total'],
                'online': stats['online'],
                'warning': stats['warning'],
                'offline': stats['offline'],
                'timestamp': datetime.now().isoformat(),
            }
        })

    except Exception as e:
        logger.error(f"Ошибка API дашборда: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)