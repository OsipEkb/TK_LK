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