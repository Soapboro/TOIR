import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('equipment', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentReliability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('failure_count', models.PositiveIntegerField(default=0, verbose_name='Количество отказов')),
                ('total_downtime_hours', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=10,
                    verbose_name='Суммарный простой (ч)',
                )),
                ('mtbf_hours', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=10,
                    null=True,
                    verbose_name='MTBF (ч) — среднее время между отказами',
                )),
                ('mttr_hours', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=10,
                    null=True,
                    verbose_name='MTTR (ч) — среднее время восстановления',
                )),
                ('availability_percent', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=5,
                    null=True,
                    verbose_name='Коэффициент готовности (%)',
                )),
                ('calculated_at', models.DateTimeField(auto_now=True, verbose_name='Дата расчёта')),
                ('equipment', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reliability',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
            ],
            options={
                'verbose_name': 'Надёжность оборудования',
                'verbose_name_plural': 'Надёжность оборудования',
            },
        ),
        migrations.CreateModel(
            name='FailurePrediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predicted_failure_date', models.DateField(verbose_name='Прогнозируемая дата отказа')),
                ('confidence_percent', models.DecimalField(
                    decimal_places=2,
                    max_digits=5,
                    verbose_name='Достоверность (%)',
                )),
                ('prediction_basis', models.TextField(blank=True, verbose_name='Основание прогноза')),
                ('is_acknowledged', models.BooleanField(default=False, verbose_name='Принято к сведению')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='failure_predictions',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
            ],
            options={
                'verbose_name': 'Прогноз неисправности',
                'verbose_name_plural': 'Прогнозы неисправностей',
                'ordering': ['predicted_failure_date'],
            },
        ),
    ]
