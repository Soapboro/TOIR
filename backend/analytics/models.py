from django.db import models

from equipment.models import Equipment


class EquipmentReliability(models.Model):
    """Показатели надёжности оборудования (пересчитываются по расписанию)."""
    equipment = models.OneToOneField(
        Equipment, on_delete=models.CASCADE,
        related_name='reliability', verbose_name='Оборудование',
    )
    failure_count = models.PositiveIntegerField(default=0, verbose_name='Количество отказов')
    total_downtime_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Суммарный простой (ч)',
    )
    mtbf_hours = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='MTBF (ч) — среднее время между отказами',
    )
    mttr_hours = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='MTTR (ч) — среднее время восстановления',
    )
    availability_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Коэффициент готовности (%)',
    )
    calculated_at = models.DateTimeField(auto_now=True, verbose_name='Дата расчёта')

    class Meta:
        verbose_name = 'Надёжность оборудования'
        verbose_name_plural = 'Надёжность оборудования'

    def __str__(self):
        return f'Надёжность: {self.equipment}'


class FailurePrediction(models.Model):
    """Прогноз неисправностей на основе исторических данных."""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='failure_predictions', verbose_name='Оборудование',
    )
    predicted_failure_date = models.DateField(verbose_name='Прогнозируемая дата отказа')
    confidence_percent = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Достоверность (%)',
    )
    prediction_basis = models.TextField(blank=True, verbose_name='Основание прогноза')
    is_acknowledged = models.BooleanField(default=False, verbose_name='Принято к сведению')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Прогноз неисправности'
        verbose_name_plural = 'Прогнозы неисправностей'
        ordering = ['predicted_failure_date']

    def __str__(self):
        return f'Прогноз для {self.equipment} — {self.predicted_failure_date}'
