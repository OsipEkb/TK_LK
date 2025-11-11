from django.db import models
from users.models import User, Organization
import uuid
from django.utils import timezone


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('truck', 'Грузовик'),
        ('car', 'Легковой автомобиль'),
        ('special', 'Спецтехника'),
        ('bus', 'Автобус'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=100, unique=True, verbose_name="Внешний ID")
    name = models.CharField(max_length=255, verbose_name="Название")
    license_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Госномер")

    # Связи
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name="Организация"
    )

    # Основные данные
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='truck', verbose_name="Тип ТС")
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name="Модель")
    year = models.IntegerField(blank=True, null=True, verbose_name="Год выпуска")

    # Текущее состояние
    current_speed = models.FloatField(default=0, verbose_name="Текущая скорость")
    fuel_level = models.FloatField(default=0, verbose_name="Уровень топлива")
    is_online = models.BooleanField(default=False, verbose_name="Онлайн")
    is_moving = models.BooleanField(default=False, verbose_name="В движении")

    # Местоположение
    last_location = models.JSONField(default=dict, blank=True, verbose_name="Последнее местоположение")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    # Временные метки - устанавливаем default=timezone.now
    last_update = models.DateTimeField(default=timezone.now, verbose_name="Последнее обновление")
    last_data_time = models.DateTimeField(blank=True, null=True, verbose_name="Время последних данных")
    last_coords_time = models.DateTimeField(blank=True, null=True, verbose_name="Время последних координат")

    # Дополнительные поля
    schema_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID схемы")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    notes = models.TextField(blank=True, null=True, verbose_name="Примечания")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Транспортное средство"
        verbose_name_plural = "Транспортные средства"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['organization']),
            models.Index(fields=['is_online']),
            models.Index(fields=['last_update']),
        ]

    def __str__(self):
        return f"{self.name} ({self.license_plate})"

    def get_status_display(self):
        if not self.is_online:
            return "offline"
        elif self.is_moving:
            return "moving"
        else:
            return "idle"


class VehicleAlert(models.Model):
    ALERT_TYPES = [
        ('overspeed', 'Превышение скорости'),
        ('fuel_theft', 'Кража топлива'),
        ('geofence', 'Выезд из геозоны'),
        ('offline', 'Потеря связи'),
        ('maintenance', 'ТО'),
    ]

    ALERT_LEVELS = [
        ('info', 'Информация'),
        ('warning', 'Предупреждение'),
        ('critical', 'Критично'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='alerts')

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Тип алерта")
    alert_level = models.CharField(max_length=20, choices=ALERT_LEVELS, verbose_name="Уровень важности")

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    # Данные алерта
    alert_data = models.JSONField(default=dict, blank=True, verbose_name="Данные алерта")

    is_resolved = models.BooleanField(default=False, verbose_name="Решено")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="Время решения")
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Кем решено"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Алерт ТС"
        verbose_name_plural = "Алерты ТС"
        indexes = [
            models.Index(fields=['vehicle', 'created_at']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['alert_type']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.get_alert_type_display()}"