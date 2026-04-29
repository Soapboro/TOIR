"""
Тесты ремонтных заявок.

Покрывает:
- POST /api/requests/              — создание заявки
- PUT  /api/requests/{id}/assign/  — назначение исполнителя
- PUT  /api/requests/{id}/status/  — смена статуса (валидные / невалидные переходы)
- Автоматическое создание уведомлений через сигналы
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from notifications.models import Notification, NotificationType
from repair_requests.models import RepairRequest, RequestStatus
from .fixtures import (
    auth_client,
    make_admin, make_manager, make_mechanic, make_operator,
    make_equipment, make_user,
)

REQUESTS_LIST = '/api/requests/'


def request_detail(pk):     return f'{REQUESTS_LIST}{pk}/'
def request_assign(pk):     return f'{REQUESTS_LIST}{pk}/assign/'
def request_status(pk):     return f'{REQUESTS_LIST}{pk}/status/'
def request_take(pk):       return f'{REQUESTS_LIST}{pk}/take/'


class CreateRequestTests(TestCase):
    """POST /api/requests/"""

    def setUp(self):
        self.operator  = make_operator()
        self.equipment = make_equipment()

    def _create(self, user=None, **overrides):
        user = user or self.operator
        payload = dict(
            equipment=self.equipment.id,
            title='Вибрация шпинделя',
            description='Повышенная вибрация при оборотах > 2000',
            priority='high',
        )
        payload.update(overrides)
        return auth_client(user).post(REQUESTS_LIST, payload, format='json')

    def test_authenticated_user_can_create(self):
        response = self._create()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_returns_401(self):
        from rest_framework.test import APIClient
        response = APIClient().post(REQUESTS_LIST, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_created_by_set_from_token(self):
        response = self._create()
        self.assertEqual(response.data['created_by'], self.operator.id)

    def test_default_status_is_new(self):
        response = self._create()
        self.assertEqual(response.data['status'], 'new')

    def test_mechanic_can_create(self):
        mechanic = make_mechanic()
        response = self._create(user=mechanic)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create(self):
        manager = make_manager()
        response = self._create(user=manager)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_persists_to_database(self):
        self._create()
        self.assertEqual(RepairRequest.objects.filter(equipment=self.equipment).count(), 1)

    def test_missing_title_returns_400(self):
        response = self._create(title='')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_equipment_returns_400(self):
        response = self._create(equipment=99999)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AssignRequestTests(TestCase):
    """PUT /api/requests/{id}/assign/"""

    def setUp(self):
        self.manager   = make_manager()
        self.mechanic  = make_mechanic()
        self.operator  = make_operator()
        self.equipment = make_equipment()
        self.req = RepairRequest.objects.create(
            equipment=self.equipment,
            title='Требует ремонта',
            description='Описание',
            priority='medium',
            created_by=self.operator,
        )

    def test_manager_can_assign(self):
        response = auth_client(self.manager).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_assign(self):
        admin = make_admin()
        response = auth_client(admin).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_operator_cannot_assign(self):
        response = auth_client(self.operator).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mechanic_cannot_assign(self):
        response = auth_client(self.mechanic).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_sets_assigned_to(self):
        auth_client(self.manager).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.req.refresh_from_db()
        self.assertEqual(self.req.assigned_to_id, self.mechanic.id)

    def test_assign_sets_status_to_assigned(self):
        auth_client(self.manager).put(
            request_assign(self.req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, RequestStatus.ASSIGNED)

    def test_assign_nonexistent_user_returns_400(self):
        response = auth_client(self.manager).put(
            request_assign(self.req.pk),
            {'user_id': 99999},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TakeRequestTests(TestCase):
    """PUT /api/requests/{id}/take/"""

    def setUp(self):
        self.mechanic = make_mechanic()
        self.other_mechanic = make_user('mechanic2@example.com', 'mechanic', username='mechanic2')
        self.manager = make_manager()
        self.operator = make_operator()
        self.equipment = make_equipment()

    def _make_request(self, created_delta=timedelta(hours=3), **overrides):
        data = dict(
            equipment=self.equipment,
            title='РќРµРЅР°Р·РЅР°С‡РµРЅРЅР°СЏ Р·Р°СЏРІРєР°',
            description='РћРїРёСЃР°РЅРёРµ',
            priority='medium',
            created_by=self.operator,
        )
        data.update(overrides)
        req = RepairRequest.objects.create(**data)
        RepairRequest.objects.filter(pk=req.pk).update(
            created_at=timezone.now() - created_delta,
        )
        req.refresh_from_db()
        return req

    def test_mechanic_can_take_old_unassigned_new_request(self):
        req = self._make_request()

        response = auth_client(self.mechanic).put(request_take(req.pk), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.assigned_to_id, self.mechanic.id)
        self.assertEqual(req.status, RequestStatus.IN_PROGRESS)

    def test_mechanic_cannot_take_before_two_hours(self):
        req = self._make_request(created_delta=timedelta(hours=1, minutes=59))

        response = auth_client(self.mechanic).put(request_take(req.pk), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        req.refresh_from_db()
        self.assertIsNone(req.assigned_to_id)
        self.assertEqual(req.status, RequestStatus.NEW)

    def test_mechanic_cannot_take_assigned_request(self):
        req = self._make_request(assigned_to=self.other_mechanic, status=RequestStatus.ASSIGNED)

        response = auth_client(self.mechanic).put(request_take(req.pk), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        req.refresh_from_db()
        self.assertEqual(req.assigned_to_id, self.other_mechanic.id)
        self.assertEqual(req.status, RequestStatus.ASSIGNED)

    def test_manager_cannot_take_request(self):
        req = self._make_request()

        response = auth_client(self.manager).put(request_take(req.pk), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mechanic_list_includes_only_old_unassigned_new_requests(self):
        old_unassigned = self._make_request(title='Р”РѕСЃС‚СѓРїРЅР°СЏ')
        fresh_unassigned = self._make_request(
            created_delta=timedelta(minutes=30),
            title='Р•С‰Рµ Р¶РґРµС‚ РјРµРЅРµРґР¶РµСЂР°',
        )
        assigned_to_other = self._make_request(
            title='Р§СѓР¶Р°СЏ',
            assigned_to=self.other_mechanic,
            status=RequestStatus.ASSIGNED,
        )

        response = auth_client(self.mechanic).get(REQUESTS_LIST)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        ids = {item['id'] for item in data}
        self.assertIn(old_unassigned.id, ids)
        self.assertNotIn(fresh_unassigned.id, ids)
        self.assertNotIn(assigned_to_other.id, ids)


class StatusTransitionTests(TestCase):
    """PUT /api/requests/{id}/status/"""

    def setUp(self):
        self.manager   = make_manager()
        self.mechanic  = make_mechanic()
        self.operator  = make_operator()
        self.equipment = make_equipment()

    def _make_assigned_request(self):
        """Создаёт заявку в статусе 'assigned' с назначенным механиком."""
        req = RepairRequest.objects.create(
            equipment=self.equipment,
            title='Ремонт',
            description='Описание',
            priority='high',
            created_by=self.operator,
        )
        # Назначаем через API, чтобы сигналы отработали
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        req.refresh_from_db()
        return req

    def test_assigned_to_in_progress_is_valid(self):
        req = self._make_assigned_request()
        response = auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.IN_PROGRESS)

    def test_unassigned_mechanic_cannot_change_status(self):
        req = self._make_assigned_request()
        other_mechanic = make_user('mechanic2@example.com', 'mechanic', username='mechanic2')
        response = auth_client(other_mechanic).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assigned_to_cancelled_is_valid(self):
        req = self._make_assigned_request()
        response = auth_client(self.manager).put(
            request_status(req.pk),
            {'status': 'cancelled'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_new_to_completed_is_invalid(self):
        req = RepairRequest.objects.create(
            equipment=self.equipment,
            title='Новая',
            description='Описание',
            priority='low',
            created_by=self.operator,
        )
        response = auth_client(self.operator).put(
            request_status(req.pk),
            {'status': 'completed'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_to_in_progress_is_invalid(self):
        req = RepairRequest.objects.create(
            equipment=self.equipment,
            title='Новая',
            description='Описание',
            priority='low',
            created_by=self.operator,
        )
        response = auth_client(self.operator).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_in_progress_to_completed_is_valid(self):
        req = self._make_assigned_request()
        # assigned → in_progress
        auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )
        # in_progress → completed
        response = auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'completed', 'resolution_notes': 'Заменена деталь'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, RequestStatus.COMPLETED)

    def test_completed_sets_completed_at(self):
        req = self._make_assigned_request()
        auth_client(self.mechanic).put(
            request_status(req.pk), {'status': 'in_progress'}, format='json',
        )
        auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'completed', 'resolution_notes': 'Готово'},
            format='json',
        )
        req.refresh_from_db()
        self.assertIsNotNone(req.completed_at)

    def test_set_status_to_assigned_via_status_endpoint_returns_400(self):
        """Статус 'assigned' доступен только через /assign/, не через /status/."""
        req = RepairRequest.objects.create(
            equipment=self.equipment,
            title='Тест',
            description='Описание',
            priority='low',
            created_by=self.operator,
        )
        response = auth_client(self.manager).put(
            request_status(req.pk),
            {'status': 'assigned'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_closed_request_cannot_change_status(self):
        req = self._make_assigned_request()
        # Доводим до closed: assigned → in_progress → completed → closed
        auth_client(self.mechanic).put(
            request_status(req.pk), {'status': 'in_progress'}, format='json',
        )
        auth_client(self.mechanic).put(
            request_status(req.pk), {'status': 'completed'}, format='json',
        )
        auth_client(self.manager).put(
            request_status(req.pk), {'status': 'closed'}, format='json',
        )
        response = auth_client(self.manager).put(
            request_status(req.pk), {'status': 'cancelled'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class NotificationOnSignalTests(TestCase):
    """
    Проверяет, что сигналы создают уведомления при изменении заявки.

    Логика (из repair_requests/signals.py):
    - При создании заявки — уведомлений нет.
    - При назначении (new→assigned, assignee добавлен):
        • REQUEST_ASSIGNED для механика
        • REQUEST_STATUS_CHANGED НЕ создаётся (подавляется сигналом)
    - При смене статуса (не связанной с назначением):
        • REQUEST_STATUS_CHANGED для создателя
        • REQUEST_STATUS_CHANGED для исполнителя (если != создатель)
    """

    def setUp(self):
        self.manager   = make_manager()
        self.mechanic  = make_mechanic()
        self.operator  = make_operator()
        self.equipment = make_equipment()

    def _create_request(self):
        return RepairRequest.objects.create(
            equipment=self.equipment,
            title='Шум редуктора',
            description='Посторонний шум при работе',
            priority='high',
            created_by=self.operator,
        )

    def test_no_notification_on_request_create(self):
        """Создание заявки не порождает уведомлений."""
        self._create_request()
        self.assertEqual(Notification.objects.count(), 0)

    def test_notification_created_on_assign(self):
        """После назначения механика создаётся 1 уведомление для него."""
        req = self._create_request()
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        notif = Notification.objects.filter(
            user=self.mechanic,
            notification_type=NotificationType.REQUEST_ASSIGNED,
        )
        self.assertEqual(notif.count(), 1)

    def test_assign_does_not_create_status_changed_notification(self):
        """При /assign/ уведомление REQUEST_STATUS_CHANGED не должно создаваться."""
        req = self._create_request()
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(
            Notification.objects.filter(
                notification_type=NotificationType.REQUEST_STATUS_CHANGED,
            ).count(),
            0,
        )

    def test_notification_created_on_status_change(self):
        """Смена статуса (assigned→in_progress) создаёт уведомление для создателя."""
        req = self._create_request()
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        Notification.objects.all().delete()  # Сбрасываем счётчик после assign

        auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )

        self.assertTrue(
            Notification.objects.filter(
                user=self.operator,
                notification_type=NotificationType.REQUEST_STATUS_CHANGED,
            ).exists()
        )

    def test_status_change_notifies_both_creator_and_assignee(self):
        """
        Смена статуса уведомляет и создателя (operator), и исполнителя (mechanic),
        так как они разные пользователи.
        """
        req = self._create_request()
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        Notification.objects.all().delete()

        auth_client(self.mechanic).put(
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )

        status_changed_notifs = Notification.objects.filter(
            notification_type=NotificationType.REQUEST_STATUS_CHANGED,
        )
        # Уведомление для создателя (operator)
        self.assertTrue(status_changed_notifs.filter(user=self.operator).exists())
        # Уведомление для исполнителя (mechanic)
        self.assertTrue(status_changed_notifs.filter(user=self.mechanic).exists())
        self.assertEqual(status_changed_notifs.count(), 2)

    def test_total_notification_count_after_full_flow(self):
        """
        Полный сценарий: создание → назначение → смена статуса.
        Итого: 3 уведомления (1 REQUEST_ASSIGNED + 2 REQUEST_STATUS_CHANGED).
        """
        req = self._create_request()  # 0 уведомлений

        auth_client(self.manager).put(  # +1 REQUEST_ASSIGNED для mechanic
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )

        auth_client(self.mechanic).put(  # +2 REQUEST_STATUS_CHANGED (operator + mechanic)
            request_status(req.pk),
            {'status': 'in_progress'},
            format='json',
        )

        self.assertEqual(Notification.objects.count(), 3)

    def test_notification_contains_request_id_as_related_object(self):
        """Уведомление о назначении содержит правильный related_object_id."""
        req = self._create_request()
        auth_client(self.manager).put(
            request_assign(req.pk),
            {'user_id': self.mechanic.id},
            format='json',
        )
        notif = Notification.objects.get(
            user=self.mechanic,
            notification_type=NotificationType.REQUEST_ASSIGNED,
        )
        self.assertEqual(notif.related_object_id, req.id)
        self.assertEqual(notif.related_object_type, 'RepairRequest')
