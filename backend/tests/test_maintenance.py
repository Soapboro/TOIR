from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from equipment.models import MaintenanceRegulation
from maintenance.models import MaintenanceHistory, MaintenancePlan, MaintenanceType, PlanStatus
from .fixtures import auth_client, make_admin, make_equipment, make_mechanic, make_operator, make_user


MAINTENANCE_RECORDS = '/api/maintenance-records/'


class MaintenanceRecordPermissionsTests(TestCase):
    def setUp(self):
        self.equipment = make_equipment()
        self.mechanic = make_mechanic()
        self.other_mechanic = make_user(
            'other.mechanic@example.com',
            'mechanic',
            full_name='Other Mechanic',
        )
        self.admin = make_admin()
        self.plan = MaintenancePlan.objects.create(
            equipment=self.equipment,
            maintenance_type=MaintenanceType.SCHEDULED,
            scheduled_date=timezone.localdate() + timedelta(days=1),
            status=PlanStatus.PLANNED,
            assigned_to=self.mechanic,
            estimated_duration_hours='2.0',
        )

    def _payload(self):
        return {
            'equipment': self.equipment.pk,
            'plan': self.plan.pk,
            'maintenance_type': MaintenanceType.SCHEDULED,
            'performed_at': timezone.now().isoformat(),
            'duration_hours': '2.0',
            'work_performed': 'Scheduled maintenance completed',
            'parts_replaced': '',
            'next_due_date': None,
        }

    def test_assigned_mechanic_can_complete_plan(self):
        response = auth_client(self.mechanic).post(
            MAINTENANCE_RECORDS,
            self._payload(),
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.COMPLETED)
        self.assertTrue(
            MaintenanceHistory.objects.filter(
                plan=self.plan,
                performed_by=self.mechanic,
            ).exists()
        )

    def test_other_mechanic_cannot_complete_assigned_plan(self):
        response = auth_client(self.other_mechanic).post(
            MAINTENANCE_RECORDS,
            self._payload(),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.PLANNED)
        self.assertFalse(MaintenanceHistory.objects.filter(plan=self.plan).exists())

    def test_admin_cannot_complete_plan_assigned_to_mechanic(self):
        response = auth_client(self.admin).post(
            MAINTENANCE_RECORDS,
            self._payload(),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, PlanStatus.PLANNED)
        self.assertFalse(MaintenanceHistory.objects.filter(plan=self.plan).exists())


class MaintenanceRegulationPermissionsTests(TestCase):
    def setUp(self):
        self.equipment = make_equipment()
        self.admin = make_admin()
        self.mechanic = make_mechanic()
        self.operator = make_operator()

    def _url(self):
        return f'/api/equipment/{self.equipment.pk}/regulations/'

    def _payload(self):
        return {
            'maintenance_type': MaintenanceType.SCHEDULED,
            'interval_days': 30,
            'description': 'Check spindle, lubrication and safety guards',
        }

    def test_admin_can_create_regulation(self):
        response = auth_client(self.admin).post(self._url(), self._payload(), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            MaintenanceRegulation.objects.filter(
                equipment=self.equipment,
                maintenance_type=MaintenanceType.SCHEDULED,
            ).exists()
        )

    def test_mechanic_can_create_regulation(self):
        response = auth_client(self.mechanic).post(self._url(), self._payload(), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(MaintenanceRegulation.objects.filter(equipment=self.equipment).exists())

    def test_operator_cannot_create_regulation(self):
        response = auth_client(self.operator).post(self._url(), self._payload(), format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(MaintenanceRegulation.objects.filter(equipment=self.equipment).exists())
