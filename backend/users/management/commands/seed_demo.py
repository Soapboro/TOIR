from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analytics.models import EquipmentReliability, FailurePrediction
from analytics.services import calculate_mtbf, predict_next_failure
from equipment.models import Equipment, EquipmentStatus, MaintenanceRegulation
from maintenance.models import (
    MaintenanceHistory,
    MaintenancePlan,
    MaintenanceSchedule,
    MaintenanceType,
    PlanStatus,
)
from notifications.models import Notification, NotificationType
from repair_requests.models import Priority, RepairRequest, RequestStatus


DEMO_DOMAIN = 'toir.demo'
DEMO_PASSWORD = 'DemoPass123!'
DEMO_INVENTORY_PREFIX = 'DEMO-'


class Command(BaseCommand):
    help = 'Create demo data for the TOIR system: users, equipment, repairs, maintenance and analytics.'

    @transaction.atomic
    def handle(self, *args, **options):
        self._delete_previous_demo()

        today = timezone.localdate()
        users = self._create_users()
        equipment = self._create_equipment(today)
        regulations = self._create_regulations(equipment)
        plans = self._create_plans(today, users, equipment, regulations)
        self._create_schedules(today, equipment, regulations)
        self._create_maintenance_history(today, users, equipment, plans)
        requests = self._create_repair_requests(today, users, equipment)
        self._create_analytics(today, equipment)
        self._create_notifications(today, users, equipment, requests, plans)

        self.stdout.write(self.style.SUCCESS('Demo data has been created.'))
        self.stdout.write('Demo credentials:')
        for user in users.values():
            self.stdout.write(f'  {user.email} / {DEMO_PASSWORD} ({user.role})')

    def _delete_previous_demo(self):
        demo_equipment = Equipment.objects.filter(inventory_number__startswith=DEMO_INVENTORY_PREFIX)
        demo_users = get_user_model().objects.filter(email__endswith=f'@{DEMO_DOMAIN}')

        Notification.objects.filter(user__in=demo_users).delete()
        EquipmentReliability.objects.filter(equipment__in=demo_equipment).delete()
        FailurePrediction.objects.filter(equipment__in=demo_equipment).delete()
        MaintenanceSchedule.objects.filter(equipment__in=demo_equipment).delete()
        MaintenanceHistory.objects.filter(equipment__in=demo_equipment).delete()
        MaintenancePlan.objects.filter(equipment__in=demo_equipment).delete()
        RepairRequest.objects.filter(equipment__in=demo_equipment).delete()
        RepairRequest.objects.filter(created_by__in=demo_users).delete()
        MaintenanceRegulation.objects.filter(equipment__in=demo_equipment).delete()
        demo_equipment.delete()
        demo_users.delete()

    def _create_users(self):
        User = get_user_model()
        specs = {
            'admin': {
                'email': f'admin@{DEMO_DOMAIN}',
                'username': 'demo_admin',
                'full_name': 'Алексей Орлов',
                'role': 'admin',
                'department': 'Администрирование',
                'phone': '+7 900 100-00-01',
                'is_staff': True,
                'is_superuser': True,
            },
            'manager': {
                'email': f'manager@{DEMO_DOMAIN}',
                'username': 'demo_manager',
                'full_name': 'Марина Соколова',
                'role': 'manager',
                'department': 'Планирование ТОиР',
                'phone': '+7 900 100-00-02',
                'is_staff': True,
            },
            'mechanic_shift_a': {
                'email': f'mechanic.a@{DEMO_DOMAIN}',
                'username': 'demo_mechanic_a',
                'full_name': 'Игорь Кузнецов',
                'role': 'mechanic',
                'department': 'Ремонтная служба, смена А',
                'phone': '+7 900 100-00-03',
            },
            'mechanic_shift_b': {
                'email': f'mechanic.b@{DEMO_DOMAIN}',
                'username': 'demo_mechanic_b',
                'full_name': 'Ольга Морозова',
                'role': 'mechanic',
                'department': 'Ремонтная служба, смена Б',
                'phone': '+7 900 100-00-04',
            },
            'operator_line_1': {
                'email': f'operator.1@{DEMO_DOMAIN}',
                'username': 'demo_operator_1',
                'full_name': 'Павел Егоров',
                'role': 'operator',
                'department': 'Цех 1',
                'phone': '+7 900 100-00-05',
            },
            'operator_line_2': {
                'email': f'operator.2@{DEMO_DOMAIN}',
                'username': 'demo_operator_2',
                'full_name': 'Елена Васильева',
                'role': 'operator',
                'department': 'Цех 2',
                'phone': '+7 900 100-00-06',
            },
        }

        users = {}
        for key, defaults in specs.items():
            user = User.objects.create(**defaults)
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=['password'])
            users[key] = user
        return users

    def _create_equipment(self, today):
        specs = [
            {
                'key': 'lathe',
                'name': 'Токарный станок ТС-16',
                'inventory_number': 'DEMO-EQ-001',
                'serial_number': 'SN-TC16-2301',
                'manufacturer': 'СтанкоМаш',
                'model': 'ТС-16',
                'category': 'Металлообработка',
                'location': 'Цех 1 / линия А',
                'installation_date': today - timedelta(days=950),
                'warranty_expiry_date': today + timedelta(days=145),
                'status': EquipmentStatus.ACTIVE,
                'specifications': {'power_kw': 11, 'spindle_rpm': 3200, 'axis_count': 2},
                'notes': 'Ключевой станок с богатой историей аварий для демонстрации MTBF.',
            },
            {
                'key': 'compressor',
                'name': 'Компрессорная станция КС-250',
                'inventory_number': 'DEMO-EQ-002',
                'serial_number': 'SN-KS250-1140',
                'manufacturer': 'ПневмоПром',
                'model': 'КС-250',
                'category': 'Компрессорное оборудование',
                'location': 'Энергоцентр',
                'installation_date': today - timedelta(days=1300),
                'warranty_expiry_date': today - timedelta(days=210),
                'status': EquipmentStatus.REPAIR,
                'specifications': {'pressure_bar': 8, 'capacity_m3_min': 42},
                'notes': 'Есть срочный прогноз отказа и критическая заявка.',
            },
            {
                'key': 'conveyor',
                'name': 'Конвейер упаковки КП-04',
                'inventory_number': 'DEMO-EQ-003',
                'serial_number': 'SN-KP04-0888',
                'manufacturer': 'ЛинияСервис',
                'model': 'КП-04',
                'category': 'Транспортировка',
                'location': 'Цех 2 / упаковка',
                'installation_date': today - timedelta(days=620),
                'warranty_expiry_date': today + timedelta(days=80),
                'status': EquipmentStatus.MAINTENANCE,
                'specifications': {'speed_m_min': 38, 'belt_width_mm': 600},
                'notes': 'Показывает плановое ТО на текущей неделе.',
            },
            {
                'key': 'robot',
                'name': 'Робот-манипулятор RM-12',
                'inventory_number': 'DEMO-EQ-004',
                'serial_number': 'SN-RM12-4412',
                'manufacturer': 'RoboTech',
                'model': 'RM-12',
                'category': 'Роботизация',
                'location': 'Цех 1 / сварочный пост',
                'installation_date': today - timedelta(days=410),
                'warranty_expiry_date': today + timedelta(days=320),
                'status': EquipmentStatus.ACTIVE,
                'specifications': {'payload_kg': 12, 'reach_mm': 1450},
                'notes': 'Мало аварийной истории: прогноз должен вернуть недостаточно данных.',
            },
            {
                'key': 'pump',
                'name': 'Насос охлаждения НО-75',
                'inventory_number': 'DEMO-EQ-005',
                'serial_number': 'SN-NO75-7780',
                'manufacturer': 'ГидроСнаб',
                'model': 'НО-75',
                'category': 'Инженерные системы',
                'location': 'Цех 3 / контур охлаждения',
                'installation_date': today - timedelta(days=1500),
                'warranty_expiry_date': today - timedelta(days=600),
                'status': EquipmentStatus.ACTIVE,
                'specifications': {'flow_m3_h': 75, 'head_m': 42},
                'notes': 'Используется для просроченных планов и отчетов.',
            },
            {
                'key': 'press',
                'name': 'Гидравлический пресс ПГ-400',
                'inventory_number': 'DEMO-EQ-006',
                'serial_number': 'SN-PG400-0505',
                'manufacturer': 'ПрессКомплект',
                'model': 'ПГ-400',
                'category': 'Прессовое оборудование',
                'location': 'Склад резерва',
                'installation_date': today - timedelta(days=2500),
                'warranty_expiry_date': today - timedelta(days=1400),
                'status': EquipmentStatus.STORAGE,
                'specifications': {'force_t': 400, 'stroke_mm': 500},
                'notes': 'Резервная единица для фильтрации по статусу и местоположению.',
            },
        ]

        equipment = {}
        for spec in specs:
            key = spec.pop('key')
            equipment[key] = Equipment.objects.create(**spec)
        return equipment

    def _create_regulations(self, equipment):
        def add(key, maintenance_type, interval_days, description):
            return MaintenanceRegulation.objects.create(
                equipment=equipment[key],
                maintenance_type=maintenance_type,
                interval_days=interval_days,
                description=description,
            )

        return {
            'lathe_inspection': add('lathe', MaintenanceType.INSPECTION, 14, 'Осмотр шпиндельного узла и направляющих.'),
            'lathe_lubrication': add('lathe', MaintenanceType.LUBRICATION, 30, 'Смазка направляющих, проверка уровня СОЖ.'),
            'compressor_scheduled': add('compressor', MaintenanceType.SCHEDULED, 45, 'Замена фильтров, контроль давления и утечек.'),
            'conveyor_inspection': add('conveyor', MaintenanceType.INSPECTION, 10, 'Осмотр ленты, роликов и датчиков безопасности.'),
            'robot_calibration': add('robot', MaintenanceType.CALIBRATION, 60, 'Калибровка осей и проверка повторяемости.'),
            'pump_overhaul': add('pump', MaintenanceType.OVERHAUL, 180, 'Ревизия рабочего колеса, подшипников и уплотнений.'),
            'press_scheduled': add('press', MaintenanceType.SCHEDULED, 90, 'Проверка гидростанции и защитных блокировок.'),
        }

    def _create_plans(self, today, users, equipment, regulations):
        plan_specs = [
            ('lathe_week', 'lathe', MaintenanceType.INSPECTION, today + timedelta(days=1), '4.0', PlanStatus.PLANNED, 'lathe_inspection', 'Плановый осмотр перед ночной сменой.'),
            ('compressor_overdue', 'compressor', MaintenanceType.SCHEDULED, today - timedelta(days=6), '6.0', PlanStatus.OVERDUE, 'compressor_scheduled', 'Просроченная замена фильтров.'),
            ('conveyor_today', 'conveyor', MaintenanceType.INSPECTION, today, '2.5', PlanStatus.IN_PROGRESS, 'conveyor_inspection', 'Идет диагностика вибрации роликов.'),
            ('robot_future', 'robot', MaintenanceType.CALIBRATION, today + timedelta(days=18), '5.0', PlanStatus.PLANNED, 'robot_calibration', 'Калибровка после переналадки оснастки.'),
            ('pump_done', 'pump', MaintenanceType.OVERHAUL, today - timedelta(days=20), '8.0', PlanStatus.COMPLETED, 'pump_overhaul', 'Капитальный ремонт выполнен.'),
            ('press_cancelled', 'press', MaintenanceType.SCHEDULED, today + timedelta(days=30), '3.0', PlanStatus.CANCELLED, 'press_scheduled', 'Отменено из-за вывода в резерв.'),
        ]

        plans = {}
        for key, eq_key, m_type, scheduled_date, duration, status, reg_key, notes in plan_specs:
            plans[key] = MaintenancePlan.objects.create(
                equipment=equipment[eq_key],
                maintenance_type=m_type,
                scheduled_date=scheduled_date,
                estimated_duration_hours=Decimal(duration),
                status=status,
                assigned_to=users['mechanic_shift_a' if eq_key in ('lathe', 'pump', 'press') else 'mechanic_shift_b'],
                regulation=regulations[reg_key],
                notes=notes,
            )
        return plans

    def _create_schedules(self, today, equipment, regulations):
        schedule_specs = [
            ('lathe_inspection', 'lathe', today + timedelta(days=1), PlanStatus.PLANNED, 'Автоматический график: ближайший осмотр.'),
            ('lathe_lubrication', 'lathe', today + timedelta(days=5), PlanStatus.PLANNED, 'Автоматический график: смазка.'),
            ('compressor_scheduled', 'compressor', today - timedelta(days=6), PlanStatus.OVERDUE, 'Автоматический график: просроченное ТО.'),
            ('conveyor_inspection', 'conveyor', today, PlanStatus.IN_PROGRESS, 'Автоматический график: выполняется сегодня.'),
            ('robot_calibration', 'robot', today + timedelta(days=7), PlanStatus.PLANNED, 'Автоматический график: калибровка на горизонте недели.'),
        ]
        for reg_key, eq_key, scheduled_date, status, notes in schedule_specs:
            MaintenanceSchedule.objects.create(
                regulation=regulations[reg_key],
                equipment=equipment[eq_key],
                scheduled_date=scheduled_date,
                status=status,
                notes=notes,
            )

    def _create_maintenance_history(self, today, users, equipment, plans):
        def aware(day, hour=9, minute=0):
            return timezone.make_aware(datetime.combine(day, time(hour, minute)))

        def record(eq_key, m_type, days_ago, performer_key, work, duration, parts='', next_due_days=None, plan_key=None, hour=10):
            return MaintenanceHistory.objects.create(
                equipment=equipment[eq_key],
                plan=plans.get(plan_key) if plan_key else None,
                maintenance_type=m_type,
                performed_at=aware(today - timedelta(days=days_ago), hour),
                performed_by=users[performer_key],
                duration_hours=Decimal(duration),
                work_performed=work,
                parts_replaced=parts,
                next_due_date=today + timedelta(days=next_due_days) if next_due_days is not None else None,
            )

        record('lathe', MaintenanceType.SCHEDULED, 58, 'mechanic_shift_a', 'Плановое ТО, протяжка крепежа, контроль люфтов.', '3.5', 'Фильтр СОЖ', 30)
        record('lathe', MaintenanceType.LUBRICATION, 25, 'mechanic_shift_a', 'Смазка направляющих и замена СОЖ.', '2.0', 'СОЖ 20 л', 5)
        record('compressor', MaintenanceType.SCHEDULED, 52, 'mechanic_shift_b', 'Замена воздушных фильтров и проверка ресивера.', '5.5', 'Комплект фильтров', -6)
        record('conveyor', MaintenanceType.INSPECTION, 11, 'mechanic_shift_b', 'Осмотр ленты, регулировка натяжения.', '1.5', '', 0)
        record('pump', MaintenanceType.OVERHAUL, 20, 'mechanic_shift_a', 'Капитальный ремонт насоса, балансировка рабочего колеса.', '7.5', 'Подшипники, торцевое уплотнение', 160, 'pump_done')
        record('robot', MaintenanceType.CALIBRATION, 75, 'mechanic_shift_b', 'Калибровка осей J1-J6.', '4.0', '', 18)

        for days_ago in (58, 38, 18):
            record('lathe', MaintenanceType.EMERGENCY, days_ago, 'mechanic_shift_a', 'Аварийный ремонт привода подачи.', '4.0', 'Датчик положения', hour=14)
        for days_ago in (80, 50, 20):
            record('compressor', MaintenanceType.EMERGENCY, days_ago, 'mechanic_shift_b', 'Аварийная остановка по перегреву компрессорного блока.', '6.5', 'Термодатчик, масло', hour=16)
        for days_ago in (100, 73, 46):
            record('pump', MaintenanceType.EMERGENCY, days_ago, 'mechanic_shift_a', 'Аварийная замена уплотнения из-за протечки.', '5.0', 'Торцевое уплотнение', hour=11)
        record('robot', MaintenanceType.EMERGENCY, 32, 'mechanic_shift_b', 'Единичный отказ энкодера оси J3.', '3.0', 'Энкодер J3', hour=15)

    def _create_repair_requests(self, today, users, equipment):
        specs = [
            ('lathe', 'Люфт суппорта после длительной смены', 'Появилась вибрация при чистовой обработке партии деталей.', Priority.HIGH, RequestStatus.IN_PROGRESS, 'operator_line_1', 'mechanic_shift_a', 1, None, ''),
            ('compressor', 'Падение давления в магистрали', 'Компрессор не держит 8 бар, срабатывает защита по перегреву.', Priority.CRITICAL, RequestStatus.ASSIGNED, 'operator_line_2', 'mechanic_shift_b', 0, None, ''),
            ('conveyor', 'Смещение упаковочной ленты', 'Лента уходит вправо, требуется регулировка роликов.', Priority.MEDIUM, RequestStatus.NEW, 'operator_line_2', None, 2, None, ''),
            ('pump', 'Подтекание после капитального ремонта', 'На фланце видны следы охлаждающей жидкости.', Priority.HIGH, RequestStatus.COMPLETED, 'operator_line_1', 'mechanic_shift_a', 12, 10, 'Подтянут фланец, заменена прокладка.'),
            ('robot', 'Периодическая ошибка позиционирования', 'Отклонение траектории при сварке тонких заготовок.', Priority.MEDIUM, RequestStatus.ON_HOLD, 'operator_line_1', 'mechanic_shift_b', 20, None, 'Ожидается поставка калибровочной плиты.'),
            ('press', 'Проверка гидравлики перед вводом в работу', 'Нужна диагностика резервного пресса перед возвращением из хранения.', Priority.LOW, RequestStatus.CANCELLED, 'manager', None, 35, None, 'Отменено: оборудование остается на складе резерва.'),
            ('lathe', 'Замена датчика положения', 'Сигнал датчика пропадает при нагреве узла.', Priority.MEDIUM, RequestStatus.CLOSED, 'operator_line_1', 'mechanic_shift_a', 65, 62, 'Датчик заменен, проведена проверка в холостом режиме.'),
            ('compressor', 'Повышенный шум подшипника', 'Шум на холостом ходу после запуска утренней смены.', Priority.HIGH, RequestStatus.CLOSED, 'operator_line_2', 'mechanic_shift_b', 95, 91, 'Подшипник заменен, вибрация в норме.'),
            ('conveyor', 'Неисправность фотодатчика', 'Фотодатчик пропускает часть коробов на высокой скорости.', Priority.MEDIUM, RequestStatus.COMPLETED, 'operator_line_2', 'mechanic_shift_b', 125, 123, 'Заменен фотодатчик, выполнена настройка чувствительности.'),
            ('pump', 'Перегрев электродвигателя', 'Температура корпуса выше нормы на 12 градусов.', Priority.CRITICAL, RequestStatus.CLOSED, 'operator_line_1', 'mechanic_shift_a', 155, 151, 'Очищен теплообменник, заменен контактор.'),
            ('robot', 'Сбой энкодера оси J3', 'После перезапуска ошибка повторяется раз в смену.', Priority.HIGH, RequestStatus.COMPLETED, 'operator_line_1', 'mechanic_shift_b', 190, 187, 'Заменен энкодер, выполнена калибровка.'),
            ('lathe', 'Плановая диагностика после аварии', 'Контроль состояния узла подачи после ремонта.', Priority.LOW, RequestStatus.CLOSED, 'manager', 'mechanic_shift_a', 240, 238, 'Отклонений не выявлено.'),
        ]

        requests = []
        for eq_key, title, description, priority, status, creator_key, assignee_key, created_days_ago, completed_days_ago, resolution in specs:
            created_at = timezone.now() - timedelta(days=created_days_ago)
            completed_at = timezone.now() - timedelta(days=completed_days_ago) if completed_days_ago is not None else None
            request = RepairRequest.objects.create(
                equipment=equipment[eq_key],
                title=title,
                description=description,
                priority=priority,
                status=status,
                created_by=users[creator_key],
                assigned_to=users[assignee_key] if assignee_key else None,
                resolution_notes=resolution,
                completed_at=completed_at,
            )
            RepairRequest.objects.filter(pk=request.pk).update(
                created_at=created_at,
                updated_at=completed_at or created_at + timedelta(hours=6),
            )
            request.refresh_from_db()
            requests.append(request)
        return requests

    def _create_analytics(self, today, equipment):
        for eq in equipment.values():
            mtbf = calculate_mtbf(eq.pk)
            failure_count = MaintenanceHistory.objects.filter(
                equipment=eq,
                maintenance_type=MaintenanceType.EMERGENCY,
            ).count()
            downtime = MaintenanceHistory.objects.filter(
                equipment=eq,
                maintenance_type=MaintenanceType.EMERGENCY,
            )
            downtime_hours = sum((record.duration_hours or Decimal('0')) for record in downtime)
            EquipmentReliability.objects.create(
                equipment=eq,
                failure_count=failure_count,
                total_downtime_hours=downtime_hours,
                mtbf_hours=Decimal(str(round(mtbf, 2))) if mtbf is not None else None,
                mttr_hours=(downtime_hours / failure_count) if failure_count else None,
                availability_percent=Decimal('98.70') if failure_count else Decimal('99.90'),
            )

            prediction = predict_next_failure(eq.pk)
            if prediction['predicted_date']:
                days_until = prediction['days_until_failure']
                confidence = Decimal('87.50') if days_until <= 7 else Decimal('73.00')
                FailurePrediction.objects.create(
                    equipment=eq,
                    predicted_failure_date=prediction['predicted_date'],
                    confidence_percent=confidence,
                    prediction_basis=(
                        f"MTBF {prediction['mtbf_hours']} ч, "
                        f"отказов в истории: {prediction['failure_count']}."
                    ),
                    is_acknowledged=days_until < 0,
                )

    def _create_notifications(self, today, users, equipment, requests, plans):
        notifications = [
            (users['mechanic_shift_b'], 'Назначена критическая заявка', 'Компрессорная станция КС-250: падение давления в магистрали.', NotificationType.REQUEST_ASSIGNED, requests[1].pk, 'RepairRequest', False),
            (users['operator_line_1'], 'Статус заявки изменен', 'Заявка по насосу охлаждения выполнена, проверьте результат работ.', NotificationType.REQUEST_STATUS_CHANGED, requests[3].pk, 'RepairRequest', False),
            (users['mechanic_shift_a'], 'Плановое ТО завтра', 'Токарный станок ТС-16: осмотр шпиндельного узла запланирован на завтра.', NotificationType.MAINTENANCE_DUE, plans['lathe_week'].pk, 'MaintenancePlan', False),
            (users['manager'], 'Просрочено ТО', 'Компрессорная станция КС-250: просрочена замена фильтров.', NotificationType.MAINTENANCE_OVERDUE, plans['compressor_overdue'].pk, 'MaintenancePlan', False),
            (users['manager'], 'Ближайший прогноз отказа', 'Для токарного станка ожидается отказ по модели MTBF в ближайшие дни.', NotificationType.FAILURE_PREDICTION, equipment['lathe'].pk, 'Equipment', False),
            (users['admin'], 'Демо-данные загружены', f'Сценарий демонстрации обновлен на {today.isoformat()}.', NotificationType.SYSTEM, None, '', True),
        ]
        for user, title, message, n_type, object_id, object_type, is_read in notifications:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=n_type,
                related_object_id=object_id,
                related_object_type=object_type,
                is_read=is_read,
            )
