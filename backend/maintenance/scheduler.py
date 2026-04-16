"""
Задачи планировщика django-apscheduler:
- Ежедневное обновление статуса просроченных планов ТО
- Рассылка напоминаний о предстоящем ТО (за 3 дня)
"""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

from .models import MaintenancePlan, PlanStatus


def mark_overdue_plans():
    today = date.today()
    updated = MaintenancePlan.objects.filter(
        scheduled_date__lt=today,
        status=PlanStatus.PLANNED,
    ).update(status=PlanStatus.OVERDUE)
    if updated:
        print(f'[scheduler] Отмечено просроченных планов: {updated}')


def send_upcoming_maintenance_reminders():
    from notifications.services import notify_maintenance_due
    reminder_date = date.today() + timedelta(days=3)
    plans = MaintenancePlan.objects.filter(
        scheduled_date=reminder_date,
        status=PlanStatus.PLANNED,
    ).select_related('assigned_to', 'equipment')
    for plan in plans:
        notify_maintenance_due(plan)
    if plans:
        print(f'[scheduler] Отправлено напоминаний о ТО: {plans.count()}')


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        mark_overdue_plans,
        trigger='cron', hour=0, minute=5,
        id='mark_overdue_plans', replace_existing=True,
    )
    scheduler.add_job(
        send_upcoming_maintenance_reminders,
        trigger='cron', hour=8, minute=0,
        id='send_upcoming_maintenance_reminders', replace_existing=True,
    )

    scheduler.start()
    print('[scheduler] Планировщик запущен.')
