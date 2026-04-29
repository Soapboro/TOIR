"""
Тесты CRUD оборудования с проверкой прав по ролям.

Покрывает:
- GET  /api/equipment/        — список (все аутентифицированные)
- POST /api/equipment/        — создание (admin / manager)
- GET  /api/equipment/{id}/   — деталь (все аутентифицированные)
- PATCH /api/equipment/{id}/  — обновление (admin / manager)
- DELETE /api/equipment/{id}/ — удаление (admin / manager)
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from equipment.models import Equipment
from .fixtures import (
    auth_client,
    make_admin, make_manager, make_mechanic, make_operator,
    make_equipment,
)

EQUIPMENT_LIST = '/api/equipment/'


def equipment_detail(pk):
    return f'{EQUIPMENT_LIST}{pk}/'


class EquipmentListTests(TestCase):
    """GET /api/equipment/"""

    def setUp(self):
        self.operator = make_operator()
        make_equipment(inventory_number='INV-001', name='Станок А')
        make_equipment(inventory_number='INV-002', name='Станок Б')

    def test_unauthenticated_returns_401(self):
        response = APIClient().get(EQUIPMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_operator_can_list(self):
        response = auth_client(self.operator).get(EQUIPMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mechanic_can_list(self):
        mechanic = make_mechanic()
        response = auth_client(mechanic).get(EQUIPMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_both_items(self):
        response = auth_client(self.operator).get(EQUIPMENT_LIST)
        # Поддерживаем как пагинированный, так и обычный ответ
        items = response.data.get('results', response.data)
        self.assertEqual(len(items), 2)

    def test_list_filter_by_status(self):
        make_equipment(inventory_number='INV-003', status='maintenance')
        response = auth_client(self.operator).get(
            EQUIPMENT_LIST, {'status': 'active'},
        )
        items = response.data.get('results', response.data)
        for item in items:
            self.assertEqual(item['status'], 'active')


class EquipmentCreateTests(TestCase):
    """POST /api/equipment/"""

    def setUp(self):
        self.admin    = make_admin()
        self.manager  = make_manager()
        self.mechanic = make_mechanic()
        self.operator = make_operator()
        self.payload = {
            'name': 'Фрезерный станок',
            'inventory_number': 'INV-NEW-001',
            'serial_number': 'SN-NEW',
            'manufacturer': 'ACME',
            'model': 'F-200',
            'status': 'active',
        }

    def _create(self, user, **overrides):
        data = {**self.payload, **overrides}
        return auth_client(user).post(EQUIPMENT_LIST, data, format='json')

    def test_admin_can_create(self):
        response = self._create(self.admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_can_create(self):
        response = self._create(self.manager, inventory_number='INV-NEW-002')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_mechanic_cannot_create(self):
        response = self._create(self.mechanic, inventory_number='INV-NEW-003')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_cannot_create(self):
        response = self._create(self.operator, inventory_number='INV-NEW-004')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_returns_id_and_inventory_number(self):
        response = self._create(self.admin)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['inventory_number'], 'INV-NEW-001')

    def test_create_persists_to_database(self):
        self._create(self.admin)
        self.assertTrue(
            Equipment.objects.filter(inventory_number='INV-NEW-001').exists()
        )

    def test_duplicate_inventory_number_returns_400(self):
        self._create(self.admin)
        response = self._create(self.admin)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_name_returns_400(self):
        response = self._create(self.admin, name='', inventory_number='INV-NEW-005')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EquipmentRetrieveTests(TestCase):
    """GET /api/equipment/{id}/"""

    def setUp(self):
        self.operator  = make_operator()
        self.equipment = make_equipment()

    def test_authenticated_can_retrieve(self):
        response = auth_client(self.operator).get(equipment_detail(self.equipment.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_contains_correct_name(self):
        response = auth_client(self.operator).get(equipment_detail(self.equipment.pk))
        self.assertEqual(response.data['name'], self.equipment.name)

    def test_retrieve_contains_inventory_number(self):
        response = auth_client(self.operator).get(equipment_detail(self.equipment.pk))
        self.assertEqual(response.data['inventory_number'], self.equipment.inventory_number)

    def test_retrieve_nonexistent_returns_404(self):
        response = auth_client(self.operator).get(equipment_detail(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_retrieve(self):
        response = APIClient().get(equipment_detail(self.equipment.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EquipmentUpdateTests(TestCase):
    """PATCH /api/equipment/{id}/"""

    def setUp(self):
        self.admin    = make_admin()
        self.manager  = make_manager()
        self.mechanic = make_mechanic()
        self.operator = make_operator()
        self.equipment = make_equipment()

    def test_admin_can_update(self):
        response = auth_client(self.admin).patch(
            equipment_detail(self.equipment.pk),
            {'name': 'Обновлённое имя'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_can_update(self):
        response = auth_client(self.manager).patch(
            equipment_detail(self.equipment.pk),
            {'location': 'Цех №2'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mechanic_cannot_update(self):
        response = auth_client(self.mechanic).patch(
            equipment_detail(self.equipment.pk),
            {'name': 'Попытка изменить'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_cannot_update(self):
        response = auth_client(self.operator).patch(
            equipment_detail(self.equipment.pk),
            {'name': 'Попытка изменить'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_persists_to_database(self):
        auth_client(self.admin).patch(
            equipment_detail(self.equipment.pk),
            {'name': 'Новое имя'},
            format='json',
        )
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.name, 'Новое имя')

    def test_update_status_field(self):
        response = auth_client(self.admin).patch(
            equipment_detail(self.equipment.pk),
            {'status': 'maintenance'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.status, 'maintenance')


class EquipmentDeleteTests(TestCase):
    """DELETE /api/equipment/{id}/"""

    def setUp(self):
        self.admin    = make_admin()
        self.manager  = make_manager()
        self.mechanic = make_mechanic()
        self.operator = make_operator()

    def test_admin_can_delete(self):
        eq = make_equipment(inventory_number='INV-DEL-1')
        response = auth_client(self.admin).delete(equipment_detail(eq.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Equipment.objects.filter(pk=eq.pk).exists())

    def test_manager_can_delete(self):
        eq = make_equipment(inventory_number='INV-DEL-2')
        response = auth_client(self.manager).delete(equipment_detail(eq.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_mechanic_cannot_delete(self):
        eq = make_equipment(inventory_number='INV-DEL-3')
        response = auth_client(self.mechanic).delete(equipment_detail(eq.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Equipment.objects.filter(pk=eq.pk).exists())

    def test_operator_cannot_delete(self):
        eq = make_equipment(inventory_number='INV-DEL-4')
        response = auth_client(self.operator).delete(equipment_detail(eq.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_returns_404(self):
        response = auth_client(self.admin).delete(equipment_detail(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
