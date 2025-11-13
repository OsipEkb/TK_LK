from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from app.api.clients import AutoGraphAPIClient
from users.models import Organization, UserAuthToken
from django.contrib.auth import get_user_model
import logging
import sys
import traceback

logger = logging.getLogger(__name__)

# Получаем кастомную модель пользователя
User = get_user_model()


# =============================================================================
# API ENDPOINTS (для мобильных приложений/внешних систем)
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def autograph_login(request):
    """
    API endpoint для аутентификации через AutoGRAPH
    Возвращает JSON ответ
    """
    print("=" * 50)
    print("🔐 API LOGIN ENDPOINT CALLED")
    print("=" * 50)

    try:
        # Шаг 0: Проверяем базовые вещи
        print("🔄 Step 0: Basic checks...")
        print(f"🔍 Request method: {request.method}")
        print(f"🔍 Content-Type: {request.content_type}")
        print(f"🔍 Request data type: {type(request.data)}")

        # Пробуем получить данные разными способами
        username = None
        password = None

        if hasattr(request, 'data') and request.data:
            username = request.data.get('username')
            password = request.data.get('password')
            print(f"🔍 From request.data: username={username}")

        if not username and request.body:
            try:
                import json
                body_data = json.loads(request.body)
                username = body_data.get('username')
                password = body_data.get('password')
                print(f"🔍 From request.body: username={username}")
            except Exception as e:
                print(f"🔍 Cannot parse request.body: {e}")

        print(f"🔍 Final: username={username}, password={'*' * len(password) if password else None}")

        if not username or not password:
            return Response({'error': 'Username and password required'}, status=400)

        # Шаг 1: Проверяем импорт AutoGraphAPIClient
        print("🔄 Step 1: Checking AutoGraphAPIClient...")
        from app.api.clients import AutoGraphAPIClient
        print("✅ AutoGraphAPIClient imported successfully")

        client = AutoGraphAPIClient()
        print("✅ AutoGraphAPIClient instance created")

        # Шаг 2: Вызов AutoGRAPH API
        print("🔄 Step 2: Calling AutoGRAPH API...")
        token = client.login(username, password)
        print(f"✅ AutoGRAPH API call completed, token received: {bool(token)}")

        if not token:
            return Response({'error': 'Invalid AutoGRAPH credentials'}, status=401)

        print(f"✅ AutoGRAPH auth successful, token length: {len(token)}")

        # Шаг 3: Работа с пользователем Django
        print("🔄 Step 3: Django user setup...")
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(username=username)
            print(f"✅ User found: {user.username}")
        except User.DoesNotExist:
            print("🔄 Creating new user...")
            user = User.objects.create_user(
                username=username,
                password=password,
                is_active=True
            )
            print(f"✅ Created new user: {user.username}")

        # Шаг 4: Сохранение токена в БД
        print("🔄 Step 4: Saving token to DB...")
        from users.models import UserAuthToken

        auth_token, created = UserAuthToken.objects.update_or_create(
            user=user,
            defaults={'token': token}
        )
        print(f"✅ Token {'created' if created else 'updated'} in DB")

        # Шаг 5: Django аутентификация
        print("🔄 Step 5: Django authentication...")
        from django.contrib.auth import authenticate, login
        django_user = authenticate(request, username=username, password=password)

        if django_user is not None:
            login(request, django_user)
            print(f"✅ Django authentication successful")
        else:
            print("❌ Django authentication failed")

        return Response({
            'success': True,
            'message': 'Authentication successful',
            'user': {'id': user.id, 'username': user.username},
            'token_saved_to_db': True,
            'django_authenticated': request.user.is_authenticated,
        })

    except Exception as e:
        print("💥" * 20)
        print("💥 UNHANDLED EXCEPTION:")
        print(f"💥 Type: {type(e).__name__}")
        print(f"💥 Message: {str(e)}")
        print("💥 Traceback:")
        import traceback
        traceback.print_exc()
        print("💥" * 20)

        return Response({
            'error': 'Internal server error',
            'exception_type': type(e).__name__,
            'exception_message': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def custom_logout(request):
    """
    API endpoint для выхода из системы
    """
    try:
        # Выход из Django
        logout(request)

        return Response({'success': True, 'message': 'Logged out'})

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({'error': 'Logout failed'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    API endpoint для получения профиля пользователя
    """
    return Response({
        'username': request.user.username,
        'email': request.user.email,
        'is_authenticated': request.user.is_authenticated,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Простой эндпоинт для проверки работы API
    """
    print("✅ Health check called - SIMPLE VERSION")
    return Response({'status': 'ok', 'message': 'Server is working'})


# =============================================================================
# HTML ENDPOINTS (для веб-интерфейса)
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class HTMLLoginView(View):
    """
    HTML форма для входа через AutoGRAPH API
    """
    template_name = 'users/login.html'

    def get(self, request):
        """
        Отображение формы входа
        """
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        """
        Обработка формы входа
        """
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"🔐 LOGIN ATTEMPT: username={username}, password={password}")

        if not username or not password:
            messages.error(request, 'Введите имя пользователя и пароль')
            return render(request, self.template_name)

        try:
            print(f"🔄 HTML Login attempt for user: {username}")

            # Аутентификация через AutoGRAPH API
            print("🔄 Creating AutoGraphAPIClient...")
            client = AutoGraphAPIClient()
            print(f"🔧 Client created with base_url: {client.base_url}")

            print("🔄 Calling client.login()...")
            token = client.login(username, password)
            print(f"🔑 Login result - token received: {bool(token)}")

            # ИСПРАВЛЕНО: проверяем что token не None и не bool
            if token and isinstance(token, str):
                print(f"🔑 Token preview: {token[:50]}")
            else:
                print(f"🔑 Token: {token}")

            if not token:
                messages.error(request, 'Неверное имя пользователя или пароль')
                print("❌ AutoGRAPH authentication failed - no token received")
                return render(request, self.template_name)

            print(f"✅ AutoGRAPH authentication successful for {username}")

            # Получаем или создаем пользователя Django
            try:
                user = User.objects.get(username=username)
                print(f"✅ User found in DB: {username}")
            except User.DoesNotExist:
                print(f"🔄 Creating new Django user: {username}")
                user = User.objects.create_user(
                    username=username,
                    password=password,  # Пароль для Django аутентификации
                    is_active=True
                )
                print(f"✅ Created new user: {username}")

            # Сохраняем токен AutoGRAPH
            print("🔄 Saving token to database...")
            UserAuthToken.objects.update_or_create(
                user=user,
                defaults={'token': token}
            )
            print(f"✅ Token saved to DB for user: {username}")

            # Аутентифицируем пользователя в Django
            print("🔄 Authenticating in Django...")
            django_user = authenticate(request, username=username, password=password)
            if django_user:
                login(request, django_user)
                print(f"✅ Django authentication successful for {username}")
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('dashboard')
            else:
                print(f"❌ Django authentication failed for {username}")
                messages.error(request, 'Ошибка аутентификации в системе')
                return render(request, self.template_name)

        except Exception as e:
            logger.error(f"HTML login error for {username}: {e}")
            print(f"💥 HTML login exception: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Ошибка входа: {str(e)}')
            return render(request, self.template_name)


@login_required
def html_logout(request):
    """
    HTML выход из системы
    """
    try:
        username = request.user.username
        logout(request)
        print(f"✅ User logged out: {username}")
        messages.success(request, 'Вы успешно вышли из системы')
    except Exception as e:
        logger.error(f"HTML logout error: {e}")
        messages.error(request, 'Ошибка при выходе из системы')

    return redirect('html_login')


# =============================================================================
# УТИЛИТЫ (можно вынести в отдельный файл позже)
# =============================================================================

def cleanup_debug_info():
    """
    Функция для очистки отладочной информации в продакшене
    TODO: Убрать все print-ы и оставить только logger
    """
    pass