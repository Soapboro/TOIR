import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_maintenanceregulation'),
        ('maintenance', '0002_maintenanceplan_regulation'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_date', models.DateField(verbose_name='Плановая дата')),
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
                    related_name='maintenance_schedules',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
                ('regulation', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='maintenance_schedules',
                    to='equipment.maintenanceregulation',
                    verbose_name='Регламент',
                )),
            ],
            options={
                'verbose_name': 'График ТО',
                'verbose_name_plural': 'Графики ТО',
                'ordering': ['scheduled_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='maintenanceschedule',
            constraint=models.UniqueConstraint(
                fields=['regulation', 'scheduled_date'],
                name='unique_regulation_scheduled_date',
            ),
        ),
    ]
