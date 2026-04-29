"""
Общие фабричные функции и базовый класс для всех тестов.
Не содержит TestCase-классов — только вспомогательный код.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from equipment.models import Equipment
from maintenance.models import MaintenanceHistory, MaintenanceType

User = get_user_model()


# ── Пользователи ──────────────────────────────────────────────────────────────

def make_user(email, role, password='testpass123', **kwargs):
    username = kwargs.pop('username', email.split('@')[0])
    full_name = kwargs.pop('full_name', f'Test {role.capitalize()}')
    return User.objects.create_user(
        email=email,
        username=username,
        password=password,
        role=role,
        full_name=full_name,
        **kwargs,
    )


def make_admin(**kwargs):
    return make_user('admin@example.com', 'admin', full_name='Admin User', **kwargs)


def make_manager(**kwargs):
    return make_user('manager@example.com', 'manager', full_name='Manager User', **kwargs)


def make_mechanic(**kwargs):
    return make_user('mechanic@example.com', 'mechanic', full_name='Mechanic User', **kwargs)


def make_operator(**kwargs):
    return make_user('operator@example.com', 'operator', full_name='Operator User', **kwargs)


# ── Оборудование ──────────────────────────────────────────────────────────────

def make_equipment(inventory_number='INV-001', **kwargs):
    defaults = dict(
        name='Токарный станок ТС-1',
        inventory_number=inventory_number,
        serial_number='SN-001',
        manufacturer='ACME',
        model='X-100',
        category='Металлообрабатывающее',
        location='Цех №1',
        status='active',
    )
    defaults.update(kwargs)
    return Equipment.objects.create(**defaults)


# ── История обслуживания ──────────────────────────────────────────────────────

def make_emergency_history(equipment, performed_at, performed_by):
    """Запись об аварийном обслуживании (используется в расчёте MTBF)."""
    return MaintenanceHistory.objects.create(
        equipment=equipment,
        maintenance_type=MaintenanceType.EMERGENCY,
        performed_at=performed_at,
        performed_by=performed_by,
        work_performed='Аварийный ремонт',
    )


def make_emergency_series(equipment, performed_by, intervals_hours):
    """
    Создаёт серию аварийных записей с заданными интервалами (в часах).
    intervals_hours = [24, 48]  →  3 записи: T, T+24h, T+72h
    """
    base = timezone.now() - timedelta(days=365)
    records = [make_emergency_history(equipment, base, performed_by)]
    current = base
    for h in intervals_hours:
        current = current + timedelta(hours=h)
        records.append(make_emergency_history(equipment, current, performed_by))
    return records


# ── Авторизованный APIClient ──────────────────────────────────────────────────

def auth_client(user):
    """Возвращает APIClient, аутентифицированный как указанный пользователь."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client
