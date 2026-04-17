from django.conf import settings
from django.db import models

from equipment.models import Equipment, MaintenanceRegulation




class MaintenanceType(models.TextChoices):
    SCHEDULED = 'scheduled', 'Плановое ТО'
    UNSCHEDULED = 'unscheduled', 'Внеплановое ТО'
    INSPECTION = 'inspection', 'Осмотр'
    CALIBRATION = 'calibration', 'Калибровка'
    LUBRICATION = 'lubrication', 'Смазка'
    OVERHAUL = 'overhaul', 'Капитальный ремонт'


class PlanStatus(models.TextChoices):
    PLANNED = 'planned', 'Запланировано'
    IN_PROGRESS = 'in_progress', 'Выполняется'
    COMPLETED = 'completed', 'Выполнено'
    OVERDUE = 'overdue', 'Просрочено'
    CANCELLED = 'cancelled', 'Отменено'


class MaintenancePlan(models.Model):
    """Запись плана-графика ТО."""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='maintenance_plans', verbose_name='Оборудование',
    )
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices, verbose_name='Вид ТО')
    scheduled_date = models.DateField(verbose_name='Плановая дата')
    estimated_duration_hours = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Плановая трудоёмкость (ч)',
    )
    status = models.CharField(
        max_length=15, choices=PlanStatus.choices,
        default=PlanStatus.PLANNED, verbose_name='Статус',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Ответственный',
    )
    regulation = models.ForeignKey(
        MaintenanceRegulation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='schedules',
        verbose_name='Регламент ТО',
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'План ТО'
        verbose_name_plural = 'Планы ТО'
        ordering = ['scheduled_date']

    def __str__(self):
        return f'{self.get_maintenance_type_display()} — {self.equipment} ({self.scheduled_date})'


class MaintenanceHistory(models.Model):
    """Запись о фактически выполненном ТО или ремонте."""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='maintenance_history', verbose_name='Оборудование',
    )
    plan = models.OneToOneField(
        MaintenancePlan, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='history_record',
        verbose_name='Связанный план',
    )
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices, verbose_name='Вид ТО')
    performed_at = models.DateTimeField(verbose_name='Дата и время выполнения')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='performed_maintenance', verbose_name='Исполнитель',
    )
    duration_hours = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name='Фактическая трудоёмкость (ч)',
    )
    work_performed = models.TextField(verbose_name='Выполненные работы')
    parts_replaced = models.TextField(blank=True, verbose_name='Замененные детали/материалы')
    next_due_date = models.DateField(null=True, blank=True, verbose_name='Дата следующего ТО')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'История ТО'
        verbose_name_plural = 'История ТО'
        ordering = ['-performed_at']

    def __str__(self):
        return f'{self.get_maintenance_type_display()} — {self.equipment} ({self.performed_at.date()})'


class MaintenanceSchedule(models.Model):
    """Автоматически сформированный график ТО на основе регламентов."""

    regulation = models.ForeignKey(
        MaintenanceRegulation, on_delete=models.CASCADE,
        related_name='maintenance_schedules', verbose_name='Регламент',
    )
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='maintenance_schedules', verbose_name='Оборудование',
    )
    scheduled_date = models.DateField(verbose_name='Плановая дата')
    status = models.CharField(
        max_length=15, choices=PlanStatus.choices,
        default=PlanStatus.PLANNED, verbose_name='Статус',
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'График ТО'
        verbose_name_plural = 'Графики ТО'
        ordering = ['scheduled_date']
        constraints = [
            models.UniqueConstraint(
                fields=['regulation', 'scheduled_date'],
                name='unique_regulation_scheduled_date',
            )
        ]

    def __str__(self):
        return (
            f'{self.regulation.get_maintenance_type_display()} — '
            f'{self.equipment} ({self.scheduled_date})'
        )
