import django_filters

from .models import RepairRequest, RequestStatus, Priority


class RepairRequestFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=RequestStatus.choices)
    priority = django_filters.ChoiceFilter(choices=Priority.choices)

    # Поиск по ответственному: ?assigned_to=<user_id>
    assigned_to = django_filters.NumberFilter(field_name='assigned_to_id')
    # Неназначенные: ?unassigned=true
    unassigned = django_filters.BooleanFilter(
        field_name='assigned_to', lookup_expr='isnull',
    )

    # Автор заявки
    created_by = django_filters.NumberFilter(field_name='created_by_id')

    # Диапазон дат создания
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    # Оборудование
    equipment = django_filters.NumberFilter(field_name='equipment_id')

    class Meta:
        model = RepairRequest
        fields = ['status', 'priority', 'assigned_to', 'equipment']
