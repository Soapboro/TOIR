from django.db import models


class MaintenanceType(models.TextChoices):
    SCHEDULED = 'scheduled', 'Плановое ТО'
    UNSCHEDULED = 'unscheduled', 'Внеплановое ТО'
    INSPECTION = 'inspection', 'Осмотр'
    CALIBRATION = 'calibration', 'Калибровка'
    LUBRICATION = 'lubrication', 'Смазка'
    OVERHAUL = 'overhaul', 'Капитальный ремонт'


class EquipmentStatus(models.TextChoices):
    ACTIVE = 'active', 'В эксплуатации'
    MAINTENANCE = 'maintenance', 'На обслуживании'
    REPAIR = 'repair', 'В ремонте'
    DECOMMISSIONED = 'decommissioned', 'Списано'
    STORAGE = 'storage', 'На складе'


class Equipment(models.Model):
    name = models.CharField(max_length=255, verbose_name='Наименование')
    inventory_number = models.CharField(max_length=100, unique=True, verbose_name='Инвентарный номер')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Серийный номер')
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name='Производитель')
    model = models.CharField(max_length=200, blank=True, verbose_name='Модель')
    category = models.CharField(max_length=100, blank=True, verbose_name='Категория')
    location = models.CharField(max_length=255, blank=True, verbose_name='Местоположение')
    installation_date = models.DateField(null=True, blank=True, verbose_name='Дата ввода в эксплуатацию')
    warranty_expiry_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания гарантии')
    status = models.CharField(
        max_length=20, choices=EquipmentStatus.choices,
        default=EquipmentStatus.ACTIVE, verbose_name='Статус',
    )
    specifications = models.JSONField(default=dict, blank=True, verbose_name='Технические характеристики')
    passport_file = models.FileField(upload_to='passports/', null=True, blank=True, verbose_name='Паспорт')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} [{self.inventory_number}]'


class MaintenanceRegulation(models.Model):
    """Регламент технического обслуживания для единицы оборудования."""
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE,
        related_name='regulations', verbose_name='Оборудование',
    )
    maintenance_type = models.CharField(
        max_length=20, choices=MaintenanceType.choices, verbose_name='Вид ТО',
    )
    interval_days = models.PositiveIntegerField(verbose_name='Интервал (дней)')
    description = models.TextField(blank=True, verbose_name='Описание работ')

    class Meta:
        verbose_name = 'Регламент ТО'
        verbose_name_plural = 'Регламенты ТО'
        ordering = ['equipment', 'interval_days']

    def __str__(self):
        return f'{self.equipment} — {self.get_maintenance_type_display()} каждые {self.interval_days} дн.'
