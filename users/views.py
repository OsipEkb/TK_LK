# users/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib import messages
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# Декоратор для проверки авторизации в AutoGRAPH
def autograph_login_required(view_func):
    """Декоратор для проверки авторизации в AutoGRAPH"""

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('autograph_token'):
            logger.warning(f"🔒 Access denied to {request.path} - no AutoGRAPH token")
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Требуется авторизация',
                    'redirect': '/auth/login/'
                }, status=401)
            # Для обычных запросов добавляем параметр next
            return redirect(f'/auth/login/?next={request.path}')

        # Проверяем, есть ли имя пользователя
        if not request.session.get('autograph_username'):
            logger.warning("AutoGRAPH token exists but no username")
            request.session.flush()
            return redirect('users:login')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """HTML форма для входа через AutoGRAPH"""

    template_name = 'users/login.html'

    def get(self, request):
        """Показать форму входа"""
        # Если уже есть токен в сессии, перенаправляем на запрошенную страницу
        token = request.session.get('autograph_token')

        if token:
            logger.info("📋 User already has token, checking where to redirect")

            # Получаем куда нужно вернуться (next параметр)
            next_url = request.GET.get('next', '/dashboard/')
            logger.info(f"📋 Redirecting to: {next_url}")

            # Перенаправляем на запрошенную страницу
            return redirect(next_url)

        return render(request, self.template_name)

    def post(self, request):
        """Обработка формы входа"""
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        logger.info(f"🔐 HTML login attempt: {username}")

        if not username or not password:
            messages.error(request, 'Введите имя пользователя и пароль')
            return render(request, self.template_name)

        try:
            # Используем наш бэкенд напрямую
            from .backend import AutoGraphAuthBackend
            backend = AutoGraphAuthBackend()
            user = backend.authenticate(request, username=username, password=password)

            if user:
                logger.info(f"✅ Backend authentication successful for {username}")

                # ОЧИЩАЕМ ВСЕ КЭШИ ПРЕДЫДУЩЕГО ПОЛЬЗОВАТЕЛЯ
                self._clear_all_previous_caches(request)

                # Вручную добавляем пользователя в запрос
                request.user = user

                # Добавляем аутентификацию в сессии
                request.session['_auth_user_id'] = str(user.pk)
                request.session['_auth_user_backend'] = 'users.backend.AutoGraphAuthBackend'
                request.session['_auth_user_hash'] = user.__dict__.get('_auth_user_hash', '')

                # ПОЛУЧАЕМ СХЕМЫ ДЛЯ НОВОГО ПОЛЬЗОВАТЕЛЯ
                logger.info(f"🔄 Getting fresh schemas for new user: {username}")
                self._update_user_schemas(request)

                # Проверяем, что схема обновилась
                schema_name = request.session.get('autograph_schema_name', 'NOT SET')

                messages.success(request, f'Добро пожаловать, {username}!')
                logger.info(f"🎉 HTML login successful for {username}")

                # Прямой редирект на запрошенную страницу или дашборд
                next_url = request.POST.get('next', '/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
                logger.error(f"❌ HTML login failed for {username}")
                return render(request, self.template_name)

        except Exception as e:
            logger.error(f"💥 HTML login error: {e}", exc_info=True)
            messages.error(request, f'Ошибка входа: {str(e)}')
            return render(request, self.template_name)

    def _clear_all_previous_caches(self, request):
        """Полная очистка всех кэшей предыдущего пользователя"""
        session = request.session
        all_keys = list(session.keys())

        # Ключи, которые нужно СОХРАНИТЬ (если есть)
        keys_to_preserve = []

        # Сначала сохраняем данные нового пользователя (если они уже есть)
        new_user_keys = []
        for key in all_keys:
            if key.startswith('_auth_') or key.startswith('autograph_'):
                # Проверяем, это данные нового или старого пользователя
                if key == 'autograph_token' and session.get(key):
                    new_user_keys.append(key)
                elif key == 'autograph_username' and session.get(key):
                    new_user_keys.append(key)
                elif key == 'autograph_authenticated' and session.get(key):
                    new_user_keys.append(key)

        logger.info(f"🧹 Clearing all previous caches. Found {len(all_keys)} keys total.")

        # Очищаем ВСЕ ключи, кроме минимально необходимых для нового пользователя
        keys_cleared = []
        for key in all_keys:
            if key not in new_user_keys and not key.startswith('csrf'):
                del session[key]
                keys_cleared.append(key)

        logger.info(f"✅ Cleared {len(keys_cleared)} previous cache keys")

    def _update_user_schemas(self, request):
        """Получение и обновление схем для текущего пользователя"""
        token = request.session.get('autograph_token')
        username = request.session.get('autograph_username')

        if not token:
            logger.error("❌ No token for schema update")
            return

        try:
            logger.info(f"🔄 Force updating schemas for user: {username}")

            # Импортируем здесь чтобы избежать циклических импортов
            from dashboard.services import AutoGraphDashboardService

            # Создаем новый сервис с токеном
            service = AutoGraphDashboardService(token=token)

            # ПРИНУДИТЕЛЬНО получаем свежие схемы
            schemas = service.get_schemas()

            if not schemas:
                logger.warning(f"⚠️ No schemas returned for user {username}")
                return

            if schemas and isinstance(schemas, list):
                if len(schemas) > 0:
                    # ОЧИЩАЕМ старые данные схем
                    for key in ['autograph_schemas', 'autograph_schema_id', 'autograph_schema_name']:
                        if key in request.session:
                            del request.session[key]

                    # Сохраняем все схемы
                    request.session['autograph_schemas'] = schemas
                    request.session['autograph_schema_id'] = schemas[0].get('ID')
                    request.session['autograph_schema_name'] = schemas[0].get('Name')

                    logger.info(f"✅ Updated schemas for {username}: Found {len(schemas)} schemas")
                else:
                    logger.warning(f"⚠️ Empty schemas list for user {username}")
                    request.session['autograph_schemas'] = []
            else:
                logger.error(f"❌ Invalid schemas data for {username}: {type(schemas)}")
                request.session['autograph_schemas'] = []

        except ImportError as e:
            logger.error(f"❌ Import error in schema update: {e}")
        except Exception as e:
            logger.error(f"💥 Error updating schemas for {username}: {e}", exc_info=True)


class APILoginView(View):
    """API для входа через AutoGRAPH"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """API вход"""
        import json

        try:
            data = json.loads(request.body.decode('utf-8'))
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()

            logger.info(f"🔐 API login attempt: {username}")

            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'error': 'Введите имя пользователя и пароль'
                })

            # Используем наш бэкенд напрямую
            from .backend import AutoGraphAuthBackend
            backend = AutoGraphAuthBackend()
            user = backend.authenticate(request, username=username, password=password)

            if user:
                logger.info(f"✅ API authentication successful for {username}")

                # Очищаем кэши предыдущего пользователя
                self._clear_all_previous_caches(request)

                # Добавляем аутентификацию в сессии
                request.session['_auth_user_id'] = str(user.pk)
                request.session['_auth_user_backend'] = 'users.backend.AutoGraphAuthBackend'
                request.session['_auth_user_hash'] = user.__dict__.get('_auth_user_hash', '')

                # Получаем схемы
                self._update_user_schemas(request)

                return JsonResponse({
                    'success': True,
                    'message': 'Авторизация успешна',
                    'data': {
                        'username': username,
                        'token': request.session.get('autograph_token', ''),
                        'schema_id': request.session.get('autograph_schema_id', ''),
                        'schema_name': request.session.get('autograph_schema_name', ''),
                        'session_key': request.session.session_key
                    }
                })
            else:
                logger.error(f"❌ API login failed for {username}")
                return JsonResponse({
                    'success': False,
                    'error': 'Неверное имя пользователя или пароль'
                })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            })
        except Exception as e:
            logger.error(f"💥 API login error: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Ошибка входа: {str(e)}'
            })

    def _clear_all_previous_caches(self, request):
        """Полная очистка всех кэшей предыдущего пользователя (для API)"""
        session = request.session
        all_keys = list(session.keys())

        # Ключи, которые нужно СОХРАНИТЬ (если есть)
        new_user_keys = []
        for key in all_keys:
            if key.startswith('csrf'):
                new_user_keys.append(key)

        logger.info(f"🧹 API: Clearing all previous caches. Found {len(all_keys)} keys total.")

        # Очищаем ВСЕ ключи, кроме CSRF
        keys_cleared = []
        for key in all_keys:
            if key not in new_user_keys:
                del session[key]
                keys_cleared.append(key)

        logger.info(f"✅ API: Cleared {len(keys_cleared)} previous cache keys")

    def _update_user_schemas(self, request):
        """Получение и обновление схем для текущего пользователя (для API)"""
        token = request.session.get('autograph_token')
        username = request.session.get('autograph_username')

        if not token:
            logger.error("❌ API: No token for schema update")
            return

        try:
            logger.info(f"🔄 API: Force updating schemas for user: {username}")

            from dashboard.services import AutoGraphDashboardService

            service = AutoGraphDashboardService(token=token)
            schemas = service.get_schemas()

            if schemas and isinstance(schemas, list) and len(schemas) > 0:
                # Очищаем старые данные схем
                for key in ['autograph_schemas', 'autograph_schema_id', 'autograph_schema_name']:
                    if key in request.session:
                        del request.session[key]

                # Сохраняем все схемы
                request.session['autograph_schemas'] = schemas
                request.session['autograph_schema_id'] = schemas[0].get('ID')
                request.session['autograph_schema_name'] = schemas[0].get('Name')

                logger.info(f"✅ API: Updated schemas for {username}")

        except Exception as e:
            logger.error(f"💥 API: Error updating schemas for {username}: {e}")


@csrf_exempt
def logout_view(request):
    """Выход из системы - РАБОТАЕТ И С GET И С POST"""
    logger.info("=== НАЧАЛО logout_view ===")
    logger.info(f"Метод запроса: {request.method}")

    username = request.session.get('autograph_username', 'unknown')
    logger.info(f"👋 Logout request from user: {username}")

    # Полностью очищаем сессию
    request.session.flush()

    # Создаем новую сессию для сообщения
    request.session.create()

    # Добавляем сообщение об успешном выходе
    messages.success(request, 'Вы успешно вышли из системы')

    logger.info("Редирект на /auth/login/")
    logger.info("=== КОНЕЦ logout_view ===")

    # Редирект на страницу входа
    return redirect('users:login')


class APILogoutView(View):
    """API для выхода из системы"""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """API выход"""
        username = request.session.get('autograph_username', 'unknown')
        logger.info(f"👋 API logout request from user: {username}")

        # Полностью очищаем сессию
        request.session.flush()

        # Создаем новую сессию
        request.session.create()

        return JsonResponse({
            'success': True,
            'message': 'Выход выполнен успешно'
        })


def check_session(request):
    """Проверка статуса сессии через API"""
    if request.session.get('autograph_token') and request.session.get('autograph_authenticated'):
        return JsonResponse({
            'authenticated': True,
            'username': request.session.get('autograph_username', ''),
            'token_exists': bool(request.session.get('autograph_token')),
            'token_length': len(request.session.get('autograph_token', '')),
            'schema_id': request.session.get('autograph_schema_id', ''),
            'schema_name': request.session.get('autograph_schema_name', ''),
            'session_key': request.session.session_key[:10] if request.session.session_key else '',
            'user_id': request.session.get('_auth_user_id', '')
        })

    return JsonResponse({
        'authenticated': False,
        'error': 'Сессия не активна'
    })


def session_info(request):
    """Информация о текущей сессии (для отладки)"""
    session_data = {
        'session_key': request.session.session_key,
        'session_expiry_age': request.session.get_expiry_age(),
        'session_expiry_date': request.session.get_expiry_date(),
        'session_modified': request.session.modified,
        'autograph_token_exists': bool(request.session.get('autograph_token')),
        'autograph_username': request.session.get('autograph_username'),
        'autograph_authenticated': request.session.get('autograph_authenticated', False),
        'autograph_schema_id': request.session.get('autograph_schema_id'),
        'autograph_schema_name': request.session.get('autograph_schema_name'),
        'all_session_keys': list(request.session.keys())
    }

    # Безопасный показ токена
    token = request.session.get('autograph_token')
    if token:
        if len(token) > 20:
            session_data['autograph_token_preview'] = f"{token[:10]}...{token[-10:]}"
        else:
            session_data['autograph_token_preview'] = token[:20]

    # Информация о пользователе Django
    if hasattr(request, 'user') and request.user.is_authenticated:
        session_data['django_user'] = {
            'id': request.user.id,
            'username': request.user.username,
            'is_authenticated': request.user.is_authenticated
        }

    return JsonResponse(session_data)


class ProfileView(View):
    """Страница профиля пользователя"""

    def get(self, request):
        """Показать профиль"""
        if not request.session.get('autograph_token'):
            return redirect(f'/auth/login/?next=/auth/profile/')

        context = {
            'username': request.session.get('autograph_username', 'Пользователь'),
            'schema_name': request.session.get('autograph_schema_name', 'Не выбрана'),
            'schema_id': request.session.get('autograph_schema_id', ''),
            'token_exists': bool(request.session.get('autograph_token')),
            'schemas': request.session.get('autograph_schemas', [])
        }

        return render(request, 'users/profile.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class ChangeSchemaView(View):
    """Изменение текущей схемы"""

    def post(self, request):
        """Смена схемы"""
        if not request.session.get('autograph_token'):
            return JsonResponse({
                'success': False,
                'error': 'Требуется авторизация'
            })

        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
            schema_id = data.get('schema_id')

            if not schema_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Не указан ID схемы'
                })

            # Ищем схему в сохраненных схемах
            schemas = request.session.get('autograph_schemas', [])
            selected_schema = None

            for schema in schemas:
                if str(schema.get('ID')) == str(schema_id):
                    selected_schema = schema
                    break

            if not selected_schema:
                return JsonResponse({
                    'success': False,
                    'error': 'Схема не найдена'
                })

            # Обновляем текущую схему в сессии
            request.session['autograph_schema_id'] = selected_schema['ID']
            request.session['autograph_schema_name'] = selected_schema.get('Name', 'Без названия')

            logger.info(
                f"🔄 User {request.session.get('autograph_username')} changed schema to: {selected_schema.get('Name')}")

            return JsonResponse({
                'success': True,
                'message': 'Схема успешно изменена',
                'data': {
                    'schema_id': selected_schema['ID'],
                    'schema_name': selected_schema.get('Name', 'Без названия')
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат JSON'
            })
        except Exception as e:
            logger.error(f"💥 Error changing schema: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка смены схемы: {str(e)}'
            })


@method_decorator(csrf_exempt, name='dispatch')
class RefreshSchemasView(View):
    """Обновление списка схем"""

    def post(self, request):
        """Обновить схемы"""
        if not request.session.get('autograph_token'):
            return JsonResponse({
                'success': False,
                'error': 'Требуется авторизация'
            })

        try:
            token = request.session.get('autograph_token')
            username = request.session.get('autograph_username')

            logger.info(f"🔄 User {username} requested schema refresh")

            from dashboard.services import AutoGraphDashboardService
            service = AutoGraphDashboardService(token=token)
            schemas = service.get_schemas()

            if not schemas:
                return JsonResponse({
                    'success': False,
                    'error': 'Не удалось получить схемы'
                })

            # Обновляем схемы в сессии
            request.session['autograph_schemas'] = schemas

            # Если текущая схема больше не существует, выбираем первую
            current_schema_id = request.session.get('autograph_schema_id')
            current_schema_exists = any(str(schema.get('ID')) == str(current_schema_id) for schema in schemas)

            if not current_schema_exists and schemas:
                request.session['autograph_schema_id'] = schemas[0].get('ID')
                request.session['autograph_schema_name'] = schemas[0].get('Name', 'Без названия')

            logger.info(f"✅ Schemas refreshed for {username}: Found {len(schemas)} schemas")

            return JsonResponse({
                'success': True,
                'message': 'Схемы успешно обновлены',
                'data': {
                    'schemas_count': len(schemas),
                    'current_schema_id': request.session.get('autograph_schema_id'),
                    'current_schema_name': request.session.get('autograph_schema_name')
                }
            })

        except Exception as e:
            logger.error(f"💥 Error refreshing schemas: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Ошибка обновления схем: {str(e)}'
            })