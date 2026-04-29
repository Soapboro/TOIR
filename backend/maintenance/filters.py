import django_filters

from .models import MaintenanceHistory, MaintenancePlan, MaintenanceSchedule, MaintenanceType, PlanStatus


class MaintenancePlanFilter(django_filters.FilterSet):
    equipment = django_filters.NumberFilter(field_name='equipment_id')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to_id')
    status = django_filters.ChoiceFilter(choices=PlanStatus.choices)
    maintenance_type = django_filters.ChoiceFilter(choices=MaintenanceType.choices)

    month = django_filters.NumberFilter(field_name='scheduled_date', lookup_expr='month')
    year = django_filters.NumberFilter(field_name='scheduled_date', lookup_expr='year')

    scheduled_after = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_before = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')

    class Meta:
        model = MaintenancePlan
        fields = ['equipment', 'assigned_to', 'status', 'maintenance_type']


class MaintenanceHistoryFilter(django_filters.FilterSet):
    equipment = django_filters.NumberFilter(field_name='equipment_id')
    performed_by = django_filters.NumberFilter(field_name='performed_by_id')
    plan = django_filters.NumberFilter(field_name='plan_id')
    maintenance_type = django_filters.ChoiceFilter(choices=MaintenanceType.choices)

    # Диапазон дат выполнения: ?performed_after=2024-01-01&performed_before=2024-12-31
    performed_after = django_filters.DateFilter(
        field_name='performed_at', lookup_expr='date__gte',
    )
    performed_before = django_filters.DateFilter(
        field_name='performed_at', lookup_expr='date__lte',
    )

    # Фильтр по дате следующего ТО: ?next_due_before=2024-06-01
    next_due_before = django_filters.DateFilter(
        field_name='next_due_date', lookup_expr='lte',
    )

    class Meta:
        model = MaintenanceHistory
        fields = ['equipment', 'performed_by', 'maintenance_type', 'plan']


class MaintenanceScheduleFilter(django_filters.FilterSet):
    equipment = django_filters.NumberFilter(field_name='equipment_id')
    status = django_filters.ChoiceFilter(choices=PlanStatus.choices)

    # Фильтр по месяцу и году плановой даты: ?month=4&year=2026
    month = django_filters.NumberFilter(field_name='scheduled_date', lookup_expr='month')
    year = django_filters.NumberFilter(field_name='scheduled_date', lookup_expr='year')

    # Диапазон плановых дат: ?scheduled_after=2026-01-01&scheduled_before=2026-12-31
    scheduled_after = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_before = django_filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')

    class Meta:
        model = MaintenanceSchedule
        fields = ['equipment', 'status']
