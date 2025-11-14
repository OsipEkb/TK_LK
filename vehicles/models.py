from django.db import models
import uuid
from django.utils import timezone


class Vehicle(models.Model):
    """Упрощенная модель транспортного средства"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=100, unique=True, verbose_name="Внешний ID")
    name = models.CharField(max_length=255, verbose_name="Название")
    license_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Госномер")

    # Текущее состояние
    current_speed = models.FloatField(default=0, verbose_name="Текущая скорость")
    fuel_level = models.FloatField(default=0, verbose_name="Уровень топлива")
    is_online = models.BooleanField(default=False, verbose_name="Онлайн")

    # Местоположение
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    # Временные метки
    last_update = models.DateTimeField(default=timezone.now, verbose_name="Последнее обновление")

    # Дополнительные поля
    schema_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID схемы")
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Транспортное средство"
        verbose_name_plural = "Транспортные средства"
        indexes = [
            models.Index(fields=['external_id']),
            models.Index(fields=['is_online']),
            models.Index(fields=['last_update']),
        ]

    def __str__(self):
        plate = self.license_plate if self.license_plate else "без номера"
        return f"{self.name} ({plate})"

    def get_status_display(self):
        """Отображение статуса ТС"""
        if not self.is_online:
            return "offline"
        elif self.current_speed > 0:
            return "moving"
        else:
            return "idle"


class VehicleDataSnapshot(models.Model):
    """Снимок данных ТС для исторического анализа"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='snapshots')

    # Данные на момент снимка
    speed = models.FloatField(default=0, verbose_name="Скорость")
    fuel_level = models.FloatField(default=0, verbose_name="Уровень топлива")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Широта")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Долгота")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")

    # Дополнительные метрики
    engine_hours = models.FloatField(default=0, verbose_name="Моточасы")
    total_distance = models.FloatField(default=0, verbose_name="Общий пробег")

    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Время снимка")

    class Meta:
        verbose_name = "Снимок данных ТС"
        verbose_name_plural = "Снимки данных ТС"
        indexes = [
            models.Index(fields=['vehicle', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.vehicle.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"