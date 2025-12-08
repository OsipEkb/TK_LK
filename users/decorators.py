from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


def autograph_login_required(view_func):
    """
    Декоратор для проверки авторизации в AutoGRAPH API
    Проверяет наличие токена в сессии Django
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Проверяем наличие токена в сессии
        token = request.session.get('autograph_token')

        if not token:
            logger.warning(f"🚫 Access denied for {request.path} - no autograph token")
            messages.error(request, 'Требуется авторизация в системе мониторинга')
            return redirect('users:login')

        # Проверяем, что пользователь аутентифицирован
        if not request.session.get('autograph_authenticated'):
            logger.warning(f"🚫 User not authenticated for {request.path}")
            messages.error(request, 'Сессия истекла. Пожалуйста, войдите снова.')
            return redirect('users:login')

        logger.debug(f"✅ Access granted for {request.path}, user: {request.session.get('autograph_username')}")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def autograph_login_required_api(view_func):
    """
    Декоратор для API endpoints - возвращает JSON вместо редиректа
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        token = request.session.get('autograph_token')

        if not token:
            logger.warning(f"🚫 API access denied for {request.path} - no token")
            return JsonResponse({
                'success': False,
                'error': 'Требуется авторизация',
                'redirect': '/auth/login/'
            }, status=401)

        if not request.session.get('autograph_authenticated'):
            logger.warning(f"🚫 API access denied for {request.path} - not authenticated")
            return JsonResponse({
                'success': False,
                'error': 'Сессия истекла',
                'redirect': '/auth/login/'
            }, status=401)

        return view_func(request, *args, **kwargs)

    return _wrapped_view