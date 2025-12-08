from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    """Базовые тесты для аутентификации"""

    def test_login_page_loads(self):
        """Тест загрузки страницы входа"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Вход в систему')

    def test_logout_redirect(self):
        """Тест редиректа на страницу входа после выхода"""
        response = self.client.get(reverse('users:logout'))
        # После выхода должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:login'))