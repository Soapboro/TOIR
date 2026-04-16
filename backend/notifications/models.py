from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    REQUEST_CREATED = 'request_created', 'Создана заявка'
    REQUEST_ASSIGNED = 'request_assigned', 'Заявка назначена'
    REQUEST_STATUS_CHANGED = 'request_status_changed', 'Статус заявки изменён'
    MAINTENANCE_DUE = 'maintenance_due', 'Плановое ТО'
    MAINTENANCE_OVERDUE = 'maintenance_overdue', 'Просрочено ТО'
    FAILURE_PREDICTION = 'failure_prediction', 'Прогноз неисправности'
    SYSTEM = 'system', 'Системное'


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications', verbose_name='Получатель',
    )
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Текст')
    notification_type = models.CharField(
        max_length=30, choices=NotificationType.choices,
        default=NotificationType.SYSTEM, verbose_name='Тип',
    )
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.title}'
