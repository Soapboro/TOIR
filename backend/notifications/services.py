"""
Сервисные функции для создания уведомлений и отправки email.
"""
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, NotificationType


def _create_notification(user, title, message, notification_type,
                          related_object_id=None, related_object_type=''):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_object_id=related_object_id,
        related_object_type=related_object_type,
    )


def _send_email_notification(user, subject, message):
    if user.is_email_notifications_enabled and user.email:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass


def notify_request_assigned(repair_request):
    if not repair_request.assigned_to:
        return
    user = repair_request.assigned_to
    title = f'Вам назначена заявка #{repair_request.pk}'
    message = (
        f'Оборудование: {repair_request.equipment}\n'
        f'Тема: {repair_request.title}\n'
        f'Приоритет: {repair_request.get_priority_display()}'
    )
    _create_notification(user, title, message, NotificationType.REQUEST_ASSIGNED,
                         related_object_id=repair_request.pk, related_object_type='RepairRequest')
    _send_email_notification(user, title, message)


def notify_request_status_changed(repair_request):
    title = f'Статус заявки #{repair_request.pk} изменён'
    message = (
        f'Оборудование: {repair_request.equipment}\n'
        f'Тема: {repair_request.title}\n'
        f'Новый статус: {repair_request.get_status_display()}'
    )
    kwargs = dict(
        notification_type=NotificationType.REQUEST_STATUS_CHANGED,
        related_object_id=repair_request.pk,
        related_object_type='RepairRequest',
    )

    # Уведомить автора заявки
    _create_notification(repair_request.created_by, title, message, **kwargs)
    _send_email_notification(repair_request.created_by, title, message)

    # Уведомить назначенного исполнителя (если есть и это не тот же человек)
    assignee = repair_request.assigned_to
    if assignee and assignee.pk != repair_request.created_by_id:
        _create_notification(assignee, title, message, **kwargs)
        _send_email_notification(assignee, title, message)


def notify_maintenance_due(plan):
    if not plan.assigned_to:
        return
    user = plan.assigned_to
    title = f'Плановое ТО: {plan.equipment}'
    message = f'Запланировано на {plan.scheduled_date}. Вид: {plan.get_maintenance_type_display()}'
    _create_notification(user, title, message, NotificationType.MAINTENANCE_DUE,
                         related_object_id=plan.pk, related_object_type='MaintenancePlan')
    _send_email_notification(user, title, message)
