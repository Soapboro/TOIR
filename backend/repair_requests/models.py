from django.conf import settings
from django.db import models

from equipment.models import Equipment


class Priority(models.TextChoices):
    LOW = 'low', 'Низкий'
    MEDIUM = 'medium', 'Средний'
    HIGH = 'high', 'Высокий'
    CRITICAL = 'critical', 'Критический'


class RequestStatus(models.TextChoices):
    NEW = 'new', 'Новая'
    IN_PROGRESS = 'in_progress', 'В работе'
    ON_HOLD = 'on_hold', 'Приостановлена'
    COMPLETED = 'completed', 'Выполнена'
    CANCELLED = 'cancelled', 'Отменена'


class RepairRequest(models.Model):
    equipment = models.ForeignKey(
        Equipment, on_delete=models.PROTECT,
        related_name='repair_requests', verbose_name='Оборудование',
    )
    title = models.CharField(max_length=255, verbose_name='Тема')
    description = models.TextField(verbose_name='Описание неисправности')
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM, verbose_name='Приоритет',
    )
    status = models.CharField(
        max_length=15, choices=RequestStatus.choices,
        default=RequestStatus.NEW, verbose_name='Статус',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_requests', verbose_name='Автор',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_requests',
        verbose_name='Ответственный исполнитель',
    )
    resolution_notes = models.TextField(blank=True, verbose_name='Описание выполненных работ')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка на ремонт'
        verbose_name_plural = 'Заявки на ремонт'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pk} — {self.title} ({self.get_priority_display()})'
