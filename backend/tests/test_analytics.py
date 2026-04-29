"""
Тесты аналитики и расчёта MTBF.

Покрывает:
- calculate_mtbf(): корректный расчёт при 2+ аварийных записях;
  возврат None при недостатке данных (0 или 1 запись).
- predict_next_failure(): прогноз при достаточных данных; None-поля при нехватке.
- Учёт только записей с типом MaintenanceType.EMERGENCY («аварийный»).
- GET /api/analytics/summary/          — структура ответа
- GET /api/analytics/requests-trend/   — 12 точек
- GET /api/analytics/equipment-stats/  — список с repair_count / mtbf_hours
- GET /api/analytics/predictions/      — требует аутентификации
"""
from datetime import timedelta, date

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from analytics.services import calculate_mtbf, predict_next_failure
from maintenance.models import MaintenanceHistory, MaintenancePlan, MaintenanceType, PlanStatus
from repair_requests.models import RepairRequest
from .fixtures import (
    auth_client,
    make_admin, make_mechanic, make_operator,
    make_equipment, make_emergency_history, make_emergency_series,
)


class CalculateMTBFTests(TestCase):
    """Модульные тесты функции analytics.services.calculate_mtbf()."""

    def setUp(self):
        self.mechanic  = make_mechanic()
        self.equipment = make_equipment()

    # ── Недостаточно данных ───────────────────────────────────────────────────

    def test_returns_none_with_zero_records(self):
        result = calculate_mtbf(self.equipment.id)
        self.assertIsNone(result)

    def test_returns_none_with_one_record(self):
        make_emergency_history(self.equipment, timezone.now(), self.mechanic)
        result = calculate_mtbf(self.equipment.id)
        self.assertIsNone(result)

    # ── Корректный расчёт ─────────────────────────────────────────────────────

    def test_correct_mtbf_with_two_records(self):
        """2 записи с интервалом 48 ч → MTBF = 48 ч."""
        base = timezone.now() - timedelta(days=60)
        make_emergency_history(self.equipment, base, self.mechanic)
        make_emergency_history(self.equipment, base + timedelta(hours=48), self.mechanic)

        result = calculate_mtbf(self.equipment.id)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 48.0, places=1)

    def test_correct_mtbf_with_three_records(self):
        """
        3 записи: T, T+24h, T+72h
        Интервалы: [24, 48]  →  MTBF = (24 + 48) / 2 = 36 ч.
        """
        # make_emergency_series создаёт N+1 записей для N интервалов
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])

        result = calculate_mtbf(self.equipment.id)

        self.assertIsNotNone(result)
        self.assertAlmostEqual(result, 36.0, places=1)

    def test_correct_mtbf_with_uniform_intervals(self):
        """4 записи с равномерным интервалом 72 ч → MTBF = 72 ч."""
        make_emergency_series(
            self.equipment, self.mechanic, intervals_hours=[72, 72, 72],
        )
        result = calculate_mtbf(self.equipment.id)
        self.assertAlmostEqual(result, 72.0, places=1)

    # ── Только аварийный тип ──────────────────────────────────────────────────

    def test_ignores_non_emergency_maintenance_records(self):
        """
        Плановые/осмотровые записи не влияют на MTBF.
        При наличии только неаварийных записей возвращает None.
        """
        base = timezone.now() - timedelta(days=30)
        for mtype in [MaintenanceType.SCHEDULED, MaintenanceType.INSPECTION]:
            MaintenanceHistory.objects.create(
                equipment=self.equipment,
                maintenance_type=mtype,
                performed_at=base,
                performed_by=self.mechanic,
                work_performed='Плановое',
            )
            base += timedelta(hours=24)

        result = calculate_mtbf(self.equipment.id)
        self.assertIsNone(result)

    def test_counts_only_emergency_records(self):
        """
        Смешанные записи: 1 аварийная + 2 плановые → MTBF = None (< 2 аварийных).
        """
        base = timezone.now() - timedelta(days=30)
        make_emergency_history(self.equipment, base, self.mechanic)

        for mtype in [MaintenanceType.SCHEDULED, MaintenanceType.LUBRICATION]:
            base += timedelta(hours=24)
            MaintenanceHistory.objects.create(
                equipment=self.equipment,
                maintenance_type=mtype,
                performed_at=base,
                performed_by=self.mechanic,
                work_performed='Плановое',
            )

        result = calculate_mtbf(self.equipment.id)
        self.assertIsNone(result)

    def test_result_is_float(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        result = calculate_mtbf(self.equipment.id)
        self.assertIsInstance(result, float)

    def test_does_not_mix_equipment(self):
        """MTBF для одного оборудования не должен зависеть от записей другого."""
        other = make_equipment(inventory_number='INV-OTHER')
        base = timezone.now() - timedelta(days=60)
        make_emergency_history(other, base, self.mechanic)
        make_emergency_history(other, base + timedelta(hours=24), self.mechanic)

        result = calculate_mtbf(self.equipment.id)
        self.assertIsNone(result)


class PredictNextFailureTests(TestCase):
    """Модульные тесты функции analytics.services.predict_next_failure()."""

    def setUp(self):
        self.mechanic  = make_mechanic()
        self.equipment = make_equipment()

    def test_returns_none_fields_with_zero_records(self):
        result = predict_next_failure(self.equipment.id)

        self.assertIsNone(result['predicted_date'])
        self.assertIsNone(result['mtbf_hours'])
        self.assertIsNone(result['days_until_failure'])
        self.assertEqual(result['failure_count'], 0)
        self.assertIsNotNone(result['reason'])

    def test_returns_none_fields_with_one_record(self):
        make_emergency_history(self.equipment, timezone.now(), self.mechanic)
        result = predict_next_failure(self.equipment.id)

        self.assertIsNone(result['predicted_date'])
        self.assertIsNone(result['days_until_failure'])
        self.assertEqual(result['failure_count'], 1)
        self.assertIsNotNone(result['last_failure_date'])

    def test_returns_prediction_with_sufficient_data(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        result = predict_next_failure(self.equipment.id)

        self.assertIsNotNone(result['predicted_date'])
        self.assertIsNotNone(result['mtbf_hours'])
        self.assertIsNotNone(result['days_until_failure'])
        self.assertIsNone(result['reason'])

    def test_failure_count_matches_records(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        result = predict_next_failure(self.equipment.id)
        self.assertEqual(result['failure_count'], 3)

    def test_predicted_date_is_date_type(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        result = predict_next_failure(self.equipment.id)
        self.assertIsInstance(result['predicted_date'], date)

    def test_mtbf_hours_matches_calculate_mtbf(self):
        """predict_next_failure.mtbf_hours должен совпадать с calculate_mtbf()."""
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        pred   = predict_next_failure(self.equipment.id)
        direct = calculate_mtbf(self.equipment.id)
        self.assertAlmostEqual(pred['mtbf_hours'], direct, places=1)

    def test_days_until_failure_is_integer(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        result = predict_next_failure(self.equipment.id)
        self.assertIsInstance(result['days_until_failure'], int)

    def test_past_failure_gives_negative_days_until_failure(self):
        """Если прогноз уже в прошлом — days_until_failure < 0."""
        # Создаём 2 исторических отказа далеко в прошлом → прогноз тоже в прошлом
        base = timezone.now() - timedelta(days=500)
        make_emergency_history(self.equipment, base, self.mechanic)
        make_emergency_history(self.equipment, base + timedelta(hours=24), self.mechanic)

        result = predict_next_failure(self.equipment.id)
        self.assertIsNotNone(result['days_until_failure'])
        self.assertLess(result['days_until_failure'], 0)


class AnalyticsSummaryAPITests(TestCase):
    """GET /api/analytics/summary/"""

    def setUp(self):
        self.admin    = make_admin()
        self.operator = make_operator()
        self.mechanic = make_mechanic()
        self.equipment = make_equipment()

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get('/api/analytics/summary/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_200_for_authenticated(self):
        response = auth_client(self.operator).get('/api/analytics/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_has_equipment_key(self):
        response = auth_client(self.operator).get('/api/analytics/summary/')
        self.assertIn('equipment', response.data)
        self.assertIn('total', response.data['equipment'])

    def test_response_has_open_requests_key(self):
        response = auth_client(self.operator).get('/api/analytics/summary/')
        self.assertIn('open_requests', response.data)

    def test_response_has_maintenance_key(self):
        response = auth_client(self.operator).get('/api/analytics/summary/')
        self.assertIn('maintenance', response.data)
        self.assertIn('this_week', response.data['maintenance'])
        self.assertIn('overdue', response.data['maintenance'])

    def test_equipment_total_reflects_database(self):
        make_equipment(inventory_number='INV-X1')
        make_equipment(inventory_number='INV-X2')
        response = auth_client(self.operator).get('/api/analytics/summary/')
        # self.equipment + 2 дополнительных = 3
        self.assertEqual(response.data['equipment']['total'], 3)

    def test_open_requests_count_is_correct(self):
        RepairRequest.objects.create(
            equipment=self.equipment, title='T1', description='D',
            priority='high', created_by=self.operator,
        )
        RepairRequest.objects.create(
            equipment=self.equipment, title='T2', description='D',
            priority='medium', created_by=self.operator,
        )
        response = auth_client(self.operator).get('/api/analytics/summary/')
        self.assertEqual(response.data['open_requests'], 2)

    def test_overdue_counts_past_planned_maintenance(self):
        MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.SCHEDULED,
            scheduled_date=timezone.localdate() - timedelta(days=1),
            status=PlanStatus.PLANNED,
            assigned_to=self.mechanic,
        )

        response = auth_client(self.operator).get('/api/analytics/summary/')

        self.assertEqual(response.data['maintenance']['overdue'], 1)


class RequestsTrendAPITests(TestCase):
    """GET /api/analytics/requests-trend/?year=YYYY"""

    def setUp(self):
        self.operator  = make_operator()
        self.equipment = make_equipment()
        self.url = '/api/analytics/requests-trend/'

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_12_months(self):
        response = auth_client(self.operator).get(self.url, {'year': 2026})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Данные могут быть пагинированы или нет
        data = response.data.get('results', response.data)
        self.assertEqual(len(data), 12)

    def test_each_month_has_required_keys(self):
        response = auth_client(self.operator).get(self.url, {'year': 2026})
        data = response.data.get('results', response.data)
        for entry in data:
            self.assertIn('month', entry)
            self.assertIn('month_label', entry)
            self.assertIn('new', entry)
            self.assertIn('completed', entry)

    def test_month_numbers_are_1_to_12(self):
        response = auth_client(self.operator).get(self.url, {'year': 2026})
        data = response.data.get('results', response.data)
        months = [entry['month'] for entry in data]
        self.assertEqual(sorted(months), list(range(1, 13)))


class EquipmentStatsListAPITests(TestCase):
    """GET /api/analytics/equipment-stats/"""

    def setUp(self):
        self.operator  = make_operator()
        self.mechanic  = make_mechanic()
        self.equipment = make_equipment()
        self.url = '/api/analytics/equipment-stats/'

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_200(self):
        response = auth_client(self.operator).get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_each_entry_has_required_fields(self):
        response = auth_client(self.operator).get(self.url)
        data = response.data.get('results', response.data)
        for entry in data:
            self.assertIn('equipment_id', entry)
            self.assertIn('equipment_name', entry)
            self.assertIn('inventory_number', entry)
            self.assertIn('repair_count', entry)
            self.assertIn('mtbf_hours', entry)

    def test_repair_count_reflects_requests(self):
        RepairRequest.objects.create(
            equipment=self.equipment, title='Сломалось',
            description='Д', priority='high', created_by=self.operator,
        )
        response = auth_client(self.operator).get(self.url)
        data = response.data.get('results', response.data)
        entry = next(e for e in data if e['equipment_id'] == self.equipment.id)
        self.assertEqual(entry['repair_count'], 1)

    def test_mtbf_null_without_emergency_records(self):
        response = auth_client(self.operator).get(self.url)
        data = response.data.get('results', response.data)
        entry = next(e for e in data if e['equipment_id'] == self.equipment.id)
        self.assertIsNone(entry['mtbf_hours'])

    def test_mtbf_calculated_with_emergency_records(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        response = auth_client(self.operator).get(self.url)
        data = response.data.get('results', response.data)
        entry = next(e for e in data if e['equipment_id'] == self.equipment.id)
        self.assertIsNotNone(entry['mtbf_hours'])
        self.assertAlmostEqual(entry['mtbf_hours'], 36.0, places=0)

    def test_sorted_by_repair_count_descending(self):
        """Оборудование с бо́льшим числом ремонтов идёт первым."""
        eq2 = make_equipment(inventory_number='INV-HIGH')
        for i in range(5):
            RepairRequest.objects.create(
                equipment=eq2, title=f'Р{i}',
                description='Д', priority='low', created_by=self.operator,
            )
        response = auth_client(self.operator).get(self.url)
        data = response.data.get('results', response.data)
        counts = [e['repair_count'] for e in data]
        self.assertEqual(counts, sorted(counts, reverse=True))


class LivePredictionsAPITests(TestCase):
    """GET /api/analytics/predictions/"""

    def setUp(self):
        self.operator  = make_operator()
        self.mechanic  = make_mechanic()
        self.equipment = make_equipment()

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get('/api/analytics/predictions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_200(self):
        response = auth_client(self.operator).get('/api/analytics/predictions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_each_entry_has_equipment_fields(self):
        response = auth_client(self.operator).get('/api/analytics/predictions/')
        data = response.data.get('results', response.data)
        for entry in data:
            self.assertIn('equipment_id', entry)
            self.assertIn('equipment_name', entry)
            self.assertIn('failure_count', entry)

    def test_equipment_without_data_has_null_predicted_date(self):
        response = auth_client(self.operator).get('/api/analytics/predictions/')
        data = response.data.get('results', response.data)
        entry = next(e for e in data if e['equipment_id'] == self.equipment.id)
        self.assertIsNone(entry['predicted_date'])

    def test_equipment_with_data_has_predicted_date(self):
        make_emergency_series(self.equipment, self.mechanic, intervals_hours=[24, 48])
        response = auth_client(self.operator).get('/api/analytics/predictions/')
        data = response.data.get('results', response.data)
        entry = next(e for e in data if e['equipment_id'] == self.equipment.id)
        self.assertIsNotNone(entry['predicted_date'])

    def test_entries_sorted_by_urgency(self):
        """
        Оборудование с прогнозом (days_until_failure не None) должно идти раньше
        оборудования без данных (None).
        """
        eq2 = make_equipment(inventory_number='INV-SORT')
        make_emergency_series(eq2, self.mechanic, intervals_hours=[24, 48])

        response = auth_client(self.operator).get('/api/analytics/predictions/')
        data = response.data.get('results', response.data)

        # Первый элемент с не-None days_until_failure, последний — None
        non_null = [e for e in data if e['days_until_failure'] is not None]
        null_entries = [e for e in data if e['days_until_failure'] is None]

        if non_null and null_entries:
            first_null_index = data.index(null_entries[0])
            last_non_null_index = max(data.index(e) for e in non_null)
            self.assertGreater(first_null_index, last_non_null_index)


class PlanFactAPITests(TestCase):
    """GET /api/analytics/plan-fact/"""

    def setUp(self):
        self.operator = make_operator()
        self.mechanic = make_mechanic()
        self.equipment = make_equipment()
        self.url = '/api/analytics/plan-fact/'

    def test_requires_authentication(self):
        from rest_framework.test import APIClient
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_totals_and_breakdowns(self):
        today = timezone.localdate()
        MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.SCHEDULED,
            scheduled_date=today,
            status=PlanStatus.COMPLETED,
            assigned_to=self.mechanic,
        )
        MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.INSPECTION,
            scheduled_date=today - timedelta(days=1),
            status=PlanStatus.OVERDUE,
            assigned_to=self.mechanic,
        )

        response = auth_client(self.operator).get(
            self.url,
            {
                'date_from': (today - timedelta(days=2)).isoformat(),
                'date_to': today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('totals', response.data)
        self.assertIn('by_type', response.data)
        self.assertIn('by_equipment', response.data)
        self.assertEqual(response.data['totals']['planned_total'], 2)
        self.assertEqual(response.data['totals']['completed'], 1)
        self.assertEqual(response.data['totals']['overdue'], 1)
        self.assertEqual(response.data['totals']['completion_percent'], 50.0)

    def test_on_time_percent_uses_executable_plan_as_denominator(self):
        today = timezone.localdate()
        completed_plan = MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.SCHEDULED,
            scheduled_date=today,
            status=PlanStatus.COMPLETED,
            assigned_to=self.mechanic,
        )
        MaintenanceHistory.objects.create(
            equipment=self.equipment,
            plan=completed_plan,
            maintenance_type=MaintenanceType.SCHEDULED,
            performed_at=timezone.now(),
            performed_by=self.mechanic,
            work_performed='Done',
        )
        MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.SCHEDULED,
            scheduled_date=today - timedelta(days=1),
            status=PlanStatus.PLANNED,
            assigned_to=self.mechanic,
        )

        response = auth_client(self.operator).get(
            self.url,
            {
                'date_from': (today - timedelta(days=1)).isoformat(),
                'date_to': today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['totals']['completed_on_time'], 1)
        self.assertEqual(response.data['totals']['overdue'], 1)
        self.assertEqual(response.data['totals']['on_time_percent'], 50.0)

    def test_invalid_period_returns_400(self):
        today = timezone.localdate()
        response = auth_client(self.operator).get(
            self.url,
            {
                'date_from': today.isoformat(),
                'date_to': (today - timedelta(days=1)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
