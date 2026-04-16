import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceRegulation',
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
                ('interval_days', models.PositiveIntegerField(verbose_name='Интервал (дней)')),
                ('description', models.TextField(blank=True, verbose_name='Описание работ')),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='regulations',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
            ],
            options={
                'verbose_name': 'Регламент ТО',
                'verbose_name_plural': 'Регламенты ТО',
                'ordering': ['equipment', 'interval_days'],
            },
        ),
    ]
