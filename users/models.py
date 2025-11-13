from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название организации")
    external_id = models.CharField(max_length=100, unique=True, verbose_name="Внешний ID")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return self.name


class User(AbstractUser):
    # ПЕРЕОПРЕДЕЛЯЕМ группы и permissions с кастомными related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # УНИКАЛЬНЫЙ related_name
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions',  # УНИКАЛЬНЫЙ related_name
        related_query_name='user',
    )

    USER_TYPE_CHOICES = (
        ('user', 'Пользователь'),
        ('admin', 'Аминистратор'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class UserAuthToken(models.Model):
    """Модель для хранения токенов AutoGRAPH API"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='autograph_token'
    )
    token = models.TextField(verbose_name="Токен AutoGRAPH")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")

    class Meta:
        verbose_name = "Токен авторизации"
        verbose_name_plural = "Токены авторизации"

    def __str__(self):
        return f"Токен для {self.user.username}"