"""
Задачи планировщика django-apscheduler:
- Ежедневное обновление статуса просроченных планов ТО
- Рассылка напоминаний о предстоящем ТО (за 3 дня)
- Автоматическое создание записей графика ТО по регламентам
"""
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

from .models import MaintenancePlan, MaintenanceSchedule, PlanStatus


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


def check_maintenance_schedules():
    """
    Для каждого регламента находит последнюю запись MaintenanceHistory.
    Если (дата последнего ТО + interval_days) <= сегодня + 7 дней —
    создаёт MaintenanceSchedule (если такая запись ещё не существует).
    """
    from equipment.models import MaintenanceRegulation
    from .models import MaintenanceHistory

    today = date.today()
    lookahead = today + timedelta(days=7)
    created_count = 0

    regulations = (
        MaintenanceRegulation.objects
        .select_related('equipment')
        .iterator()
    )

    for regulation in regulations:
        last_record = (
            MaintenanceHistory.objects
            .filter(
                equipment=regulation.equipment,
                maintenance_type=regulation.maintenance_type,
            )
            .order_by('-performed_at')
            .first()
        )

        if last_record:
            base_date = last_record.performed_at.date()
        else:
            # Нет истории — отсчитываем от даты ввода в эксплуатацию или от сегодня
            base_date = regulation.equipment.installation_date or today

        next_due = base_date + timedelta(days=regulation.interval_days)

        if next_due <= lookahead:
            status = PlanStatus.OVERDUE if next_due < today else PlanStatus.PLANNED
            _, created = MaintenanceSchedule.objects.get_or_create(
                regulation=regulation,
                scheduled_date=next_due,
                defaults={
                    'equipment': regulation.equipment,
                    'status': status,
                },
            )
            if created:
                created_count += 1

    if created_count:
        print(f'[scheduler] Создано записей графика ТО: {created_count}')


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
    scheduler.add_job(
        check_maintenance_schedules,
        trigger='cron', hour=1, minute=0,
        id='check_maintenance_schedules', replace_existing=True,
    )

    scheduler.start()
    print('[scheduler] Планировщик запущен.')
