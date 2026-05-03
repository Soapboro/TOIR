"""
Тесты аутентификации и авторизации.

Покрывает:
- POST /api/auth/register/   — регистрация
- POST /api/auth/login/      — логин, получение JWT
- GET  /api/auth/me/         — профиль текущего пользователя
- Доступ без токена          — 401
- Доступ с неподходящей ролью — 403
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .fixtures import auth_client, make_admin, make_manager, make_mechanic, make_operator, make_equipment

AUTH_REGISTER = '/api/auth/register/'
AUTH_LOGIN    = '/api/auth/login/'
AUTH_ME       = '/api/auth/me/'
EQUIPMENT_LIST = '/api/equipment/'
USERS_LIST = '/api/users/'
User = get_user_model()


class RegisterTests(TestCase):
    """POST /api/auth/register/"""

    def setUp(self):
        self.client = APIClient()

    def _register(self, **overrides):
        payload = dict(
            email='new@example.com',
            username='newuser',
            full_name='New User',
            password='StrongPass123!',
        )
        payload.update(overrides)
        return self.client.post(AUTH_REGISTER, payload, format='json')

    def test_register_success_returns_201(self):
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_response_contains_user_fields(self):
        """RegisterView возвращает объект пользователя напрямую (без вложенного 'user')."""
        response = self._register()
        self.assertIn('id', response.data)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], 'new@example.com')

    def test_register_duplicate_email_returns_400(self):
        self._register()
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_returns_400(self):
        response = self._register(email='')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_password_returns_400(self):
        response = self._register(password='')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_default_role_is_operator(self):
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'operator')


class LoginTests(TestCase):
    """POST /api/auth/login/"""

    def setUp(self):
        self.client = APIClient()
        self.user = make_operator(email='login@example.com')

    def test_login_success_returns_200(self):
        response = self.client.post(
            AUTH_LOGIN,
            {'email': 'login@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            AUTH_LOGIN,
            {'email': 'login@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_response_contains_user_data(self):
        response = self.client.post(
            AUTH_LOGIN,
            {'email': 'login@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'login@example.com')

    def test_login_wrong_password_returns_401(self):
        response = self.client.post(
            AUTH_LOGIN,
            {'email': 'login@example.com', 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user_returns_401(self):
        response = self.client.post(
            AUTH_LOGIN,
            {'email': 'ghost@example.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_empty_credentials_returns_400(self):
        response = self.client.post(AUTH_LOGIN, {}, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED,
        ])


class UnauthenticatedAccessTests(TestCase):
    """Доступ к защищённым ресурсам без токена должен возвращать 401."""

    def setUp(self):
        self.client = APIClient()

    def test_equipment_list_without_token_returns_401(self):
        response = self.client.get(EQUIPMENT_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_requests_list_without_token_returns_401(self):
        response = self.client.get('/api/requests/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_maintenance_plans_without_token_returns_401(self):
        response = self.client.get('/api/maintenance/plans/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_notifications_without_token_returns_401(self):
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_without_token_returns_401(self):
        response = self.client.get(AUTH_ME)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeEndpointTests(TestCase):
    """GET /api/auth/me/ — профиль текущего пользователя."""

    def setUp(self):
        self.operator = make_operator()
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

    def test_me_returns_200(self):
        response = self.client.get(AUTH_ME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_returns_correct_email(self):
        response = self.client.get(AUTH_ME)
        self.assertEqual(response.data['email'], self.operator.email)

    def test_me_returns_correct_role(self):
        response = self.client.get(AUTH_ME)
        self.assertEqual(response.data['role'], 'operator')


class AdminUserManagementTests(TestCase):
    """POST /api/users/ — создание пользователей администратором."""

    def setUp(self):
        self.admin = make_admin()
        self.manager = make_manager()
        self.payload = {
            'email': 'created@example.com',
            'username': 'created',
            'full_name': 'Created User',
            'password': 'StrongPass123!',
            'role': 'mechanic',
        }

    def test_admin_can_create_user(self):
        response = auth_client(self.admin).post(USERS_LIST, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='created@example.com').exists())
        self.assertEqual(response.data['role'], 'mechanic')

    def test_non_admin_cannot_create_user(self):
        response = auth_client(self.manager).post(USERS_LIST, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RoleBasedAccessTests(TestCase):
    """Проверка отказов при доступе с недостаточными правами (403)."""

    def setUp(self):
        self.admin    = make_admin()
        self.manager  = make_manager()
        self.mechanic = make_mechanic()
        self.operator = make_operator()
        self.equipment_payload = {
            'name': 'Станок',
            'inventory_number': 'INV-TEST-001',
            'status': 'active',
        }

    def _client(self, user):
        c = APIClient()
        c.force_authenticate(user=user)
        return c

    # ── Создание оборудования ─────────────────────────────────────────────────

    def test_admin_can_create_equipment(self):
        response = self._client(self.admin).post(
            EQUIPMENT_LIST, self.equipment_payload, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_cannot_create_equipment(self):
        self.equipment_payload['inventory_number'] = 'INV-TEST-002'
        response = self._client(self.manager).post(
            EQUIPMENT_LIST, self.equipment_payload, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mechanic_cannot_create_equipment(self):
        response = self._client(self.mechanic).post(
            EQUIPMENT_LIST, self.equipment_payload, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_cannot_create_equipment(self):
        response = self._client(self.operator).post(
            EQUIPMENT_LIST, self.equipment_payload, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Удаление оборудования ─────────────────────────────────────────────────

    def test_operator_cannot_delete_equipment(self):
        equipment = make_equipment()
        response = self._client(self.operator).delete(
            f'{EQUIPMENT_LIST}{equipment.id}/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Назначение заявки ─────────────────────────────────────────────────────

    def test_operator_cannot_assign_request(self):
        from repair_requests.models import RepairRequest
        equipment = make_equipment(inventory_number='INV-A-001')
        req = RepairRequest.objects.create(
            equipment=equipment,
            title='Test request',
            description='Desc',
            priority='medium',
            created_by=self.operator,
        )
        response = self._client(self.operator).put(
            f'/api/requests/{req.id}/assign/',
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mechanic_cannot_assign_request(self):
        from repair_requests.models import RepairRequest
        equipment = make_equipment(inventory_number='INV-A-002')
        req = RepairRequest.objects.create(
            equipment=equipment,
            title='Test request',
            description='Desc',
            priority='medium',
            created_by=self.operator,
        )
        response = self._client(self.mechanic).put(
            f'/api/requests/{req.id}/assign/',
            {'user_id': self.mechanic.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
