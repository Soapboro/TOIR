import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('equipment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenancePlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_type', models.CharField(
                    choices=[
                        ('scheduled', 'Плановое ТО'),
                        ('unscheduled', 'Внеплановое ТО'),
                        ('inspection', 'Осмотр'),
                        ('calibration', 'Калибровка'),
                        ('lubrication', 'Смазка'),
                        ('overhaul', 'Капитальный ремонт'),
                    ],
                    max_length=20,
                    verbose_name='Вид ТО',
                )),
                ('scheduled_date', models.DateField(verbose_name='Плановая дата')),
                ('estimated_duration_hours', models.DecimalField(
                    blank=True,
                    decimal_places=1,
                    max_digits=5,
                    null=True,
                    verbose_name='Плановая трудоёмкость (ч)',
                )),
                ('status', models.CharField(
                    choices=[
                        ('planned', 'Запланировано'),
                        ('in_progress', 'Выполняется'),
                        ('completed', 'Выполнено'),
                        ('overdue', 'Просрочено'),
                        ('cancelled', 'Отменено'),
                    ],
                    default='planned',
                    max_length=15,
                    verbose_name='Статус',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='maintenance_plans',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Ответственный',
                )),
            ],
            options={
                'verbose_name': 'План ТО',
                'verbose_name_plural': 'Планы ТО',
                'ordering': ['scheduled_date'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('maintenance_type', models.CharField(
                    choices=[
                        ('scheduled', 'Плановое ТО'),
                        ('unscheduled', 'Внеплановое ТО'),
                        ('inspection', 'Осмотр'),
                        ('calibration', 'Калибровка'),
                        ('lubrication', 'Смазка'),
                        ('overhaul', 'Капитальный ремонт'),
                    ],
                    max_length=20,
                    verbose_name='Вид ТО',
                )),
                ('performed_at', models.DateTimeField(verbose_name='Дата и время выполнения')),
                ('duration_hours', models.DecimalField(
                    blank=True,
                    decimal_places=1,
                    max_digits=5,
                    null=True,
                    verbose_name='Фактическая трудоёмкость (ч)',
                )),
                ('work_performed', models.TextField(verbose_name='Выполненные работы')),
                ('parts_replaced', models.TextField(blank=True, verbose_name='Замененные детали/материалы')),
                ('next_due_date', models.DateField(blank=True, null=True, verbose_name='Дата следующего ТО')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='maintenance_history',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
                ('plan', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='history_record',
                    to='maintenance.maintenanceplan',
                    verbose_name='Связанный план',
                )),
                ('performed_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='performed_maintenance',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Исполнитель',
                )),
            ],
            options={
                'verbose_name': 'История ТО',
                'verbose_name_plural': 'История ТО',
                'ordering': ['-performed_at'],
            },
        ),
    ]
