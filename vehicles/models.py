# vehicles/models.py - обновленные модели
from django.db import models
from django.contrib.auth.models import User
import json


class AutoGraphConnection(models.Model):
    """Настройки подключения к AutoGRAPH"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField("Токен сессии")
    schema_id = models.CharField("ID схемы", max_length=100, blank=True)
    schema_name = models.CharField("Название схемы", max_length=200, blank=True)
    last_sync = models.DateTimeField("Последняя синхронизация", auto_now=True)

    class Meta:
        verbose_name = "Подключение AutoGRAPH"
        verbose_name_plural = "Подключения AutoGRAPH"


class Vehicle(models.Model):
    """Транспортное средство"""
    connection = models.ForeignKey(AutoGraphConnection, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_id = models.CharField("ID в AutoGRAPH", max_length=100, unique=True)
    name = models.CharField("Название", max_length=200)
    license_plate = models.CharField("Госномер", max_length=50, blank=True)
    serial = models.CharField("Серийный номер", max_length=100, blank=True)
    type = models.CharField("Тип", max_length=100, blank=True)
    model = models.CharField("Модель", max_length=100, blank=True)
    group = models.CharField("Группа", max_length=100, blank=True)

    # Данные для анализа
    available_parameters = models.JSONField("Доступные параметры", default=dict)
    last_update = models.DateTimeField("Последнее обновление", auto_now=True)

    class Meta:
        verbose_name = "Транспортное средство"
        verbose_name_plural = "Транспортные средства"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.license_plate or '—'})"


class RawTrackData(models.Model):
    """Сырые данные трека"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='raw_tracks')
    timestamp = models.DateTimeField("Время", db_index=True)
    latitude = models.FloatField("Широта", null=True, blank=True)
    longitude = models.FloatField("Долгота", null=True, blank=True)
    altitude = models.FloatField("Высота", null=True, blank=True)
    speed = models.FloatField("Скорость", null=True, blank=True)
    satellites = models.IntegerField("Спутники", null=True, blank=True)
    hdop = models.FloatField("HDOP", null=True, blank=True)

    # Датчики
    engine_temp = models.FloatField("Температура двигателя", null=True, blank=True)
    fuel_level = models.FloatField("Уровень топлива", null=True, blank=True)
    voltage = models.FloatField("Напряжение", null=True, blank=True)
    rpm = models.FloatField("Обороты", null=True, blank=True)

    # Параметры
    parameters_json = models.JSONField("Параметры", default=dict)

    # Статусы
    ignition = models.BooleanField("Зажигание", default=False)
    movement = models.BooleanField("Движение", default=False)
    gps_valid = models.BooleanField("GPS валиден", default=False)

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Сырые данные трека"
        verbose_name_plural = "Сырые данные треков"
        indexes = [
            models.Index(fields=['vehicle', 'timestamp']),
            models.Index(fields=['vehicle', '-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.vehicle.name} - {self.timestamp}"


class DataCache(models.Model):
    """Кэш данных для ускорения доступа"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='cache')
    period_key = models.CharField("Ключ периода", max_length=100, db_index=True)
    data_type = models.CharField("Тип данных", max_length=50)

    # Данные
    compressed_data = models.BinaryField("Сжатые данные")
    data_size = models.IntegerField("Размер данных")
    record_count = models.IntegerField("Количество записей")

    # Метаданные
    date_from = models.DateField("Дата начала")
    date_to = models.DateField("Дата окончания")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    expires_at = models.DateTimeField("Истекает")

    class Meta:
        verbose_name = "Кэш данных"
        verbose_name_plural = "Кэши данных"
        indexes = [
            models.Index(fields=['period_key']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle.name} - {self.period_key}"


class HistoricalData(models.Model):
    """Исторические данные ТС"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='historical_data')

    # Период данных
    start_date = models.DateField("Дата начала")
    end_date = models.DateField("Дата окончания")

    # Тип данных
    DATA_TYPES = [
        ('trip_items', 'Точки трека'),
        ('trips', 'Рейсы'),
        ('fuel', 'Топливо'),
        ('mileage', 'Пробег'),
    ]
    data_type = models.CharField("Тип данных", max_length=20, choices=DATA_TYPES)

    # Сами данные
    raw_data = models.JSONField("Сырые данные", default=dict)
    processed_data = models.JSONField("Обработанные данные", default=dict)

    # Метрики для быстрого доступа
    summary = models.JSONField("Сводка", default=dict)

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Исторические данные"
        verbose_name_plural = "Исторические данные"
        indexes = [
            models.Index(fields=['vehicle', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.vehicle.name} ({self.start_date} - {self.end_date})"


class ChartConfiguration(models.Model):
    """Конфигурация диаграмм"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField("Название", max_length=100)
    chart_type = models.CharField("Тип диаграммы", max_length=50)

    # Настройки
    config = models.JSONField("Конфигурация", default=dict)

    # Параметры
    parameters = models.JSONField("Параметры", default=list)

    # Фильтры
    filters = models.JSONField("Фильтры", default=dict)

    is_default = models.BooleanField("По умолчанию", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Конфигурация диаграммы"
        verbose_name_plural = "Конфигурации диаграмм"

    def __str__(self):
        return f"{self.name} ({self.chart_type})"


class AnalysisReport(models.Model):
    """Отчет анализа"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField("Название", max_length=200)

    # Данные отчета
    vehicles = models.JSONField("ТС", default=list)
    period = models.JSONField("Период", default=dict)

    # Результаты анализа
    fuel_analysis = models.JSONField("Анализ топлива", default=dict)
    mileage_analysis = models.JSONField("Анализ пробега", default=dict)
    engine_analysis = models.JSONField("Анализ двигателя", default=dict)
    signals_analysis = models.JSONField("Анализ сигналов", default=dict)

    # Визуализация
    charts = models.JSONField("Диаграммы", default=dict)

    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Отчет анализа"
        verbose_name_plural = "Отчеты анализа"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.date()})"