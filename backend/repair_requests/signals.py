"""
Сигналы RepairRequest.

pre_save  — сохраняет предыдущие значения status и assigned_to_id на инстансе.
post_save — создаёт уведомления при изменении статуса или смене исполнителя.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


@receiver(pre_save, sender='repair_requests.RepairRequest')
def capture_previous_state(sender, instance, **kwargs):
    """Запоминаем старые значения до сохранения."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._previous_status = old.status
            instance._previous_assigned_to_id = old.assigned_to_id
        except sender.DoesNotExist:
            instance._previous_status = None
            instance._previous_assigned_to_id = None
    else:
        instance._previous_status = None
        instance._previous_assigned_to_id = None


@receiver(post_save, sender='repair_requests.RepairRequest')
def handle_request_saved(sender, instance, created, **kwargs):
    """Создаём уведомления после сохранения."""
    from notifications.services import (
        notify_request_assigned,
        notify_request_status_changed,
    )

    if created:
        return

    prev_status = getattr(instance, '_previous_status', None)
    prev_assigned_id = getattr(instance, '_previous_assigned_to_id', None)

    assignee_changed = (
        instance.assigned_to_id is not None
        and instance.assigned_to_id != prev_assigned_id
    )
    status_changed = prev_status is not None and prev_status != instance.status

    # Уведомить нового исполнителя о назначении
    if assignee_changed:
        notify_request_assigned(instance)

    # Уведомить участников о смене статуса (если это не само назначение)
    if status_changed and not (assignee_changed and instance.status == 'assigned'):
        notify_request_status_changed(instance)
