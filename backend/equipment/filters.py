import django_filters

from .models import Equipment, EquipmentStatus


class EquipmentFilter(django_filters.FilterSet):
    # Точное совпадение по статусу (значение из EquipmentStatus)
    status = django_filters.ChoiceFilter(choices=EquipmentStatus.choices)

    # Нечёткий поиск по местоположению и категории
    location = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='icontains')

    # Диапазон дат ввода в эксплуатацию
    installation_date_from = django_filters.DateFilter(
        field_name='installation_date', lookup_expr='gte',
    )
    installation_date_to = django_filters.DateFilter(
        field_name='installation_date', lookup_expr='lte',
    )

    # Признак истечения гарантии: warranty_expired=true → только просроченные
    warranty_expired = django_filters.BooleanFilter(
        field_name='warranty_expiry_date', method='filter_warranty_expired',
    )

    class Meta:
        model = Equipment
        fields = ['status', 'location', 'category']

    def filter_warranty_expired(self, queryset, name, value):
        from django.utils import timezone
        today = timezone.localdate()
        if value:
            return queryset.filter(warranty_expiry_date__lt=today)
        return queryset.filter(warranty_expiry_date__gte=today)
