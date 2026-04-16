import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Наименование')),
                ('inventory_number', models.CharField(max_length=100, unique=True, verbose_name='Инвентарный номер')),
                ('serial_number', models.CharField(blank=True, max_length=100, verbose_name='Серийный номер')),
                ('manufacturer', models.CharField(blank=True, max_length=200, verbose_name='Производитель')),
                ('model', models.CharField(blank=True, max_length=200, verbose_name='Модель')),
                ('category', models.CharField(blank=True, max_length=100, verbose_name='Категория')),
                ('location', models.CharField(blank=True, max_length=255, verbose_name='Местоположение')),
                ('installation_date', models.DateField(blank=True, null=True, verbose_name='Дата ввода в эксплуатацию')),
                ('warranty_expiry_date', models.DateField(blank=True, null=True, verbose_name='Дата окончания гарантии')),
                ('status', models.CharField(
                    choices=[
                        ('active', 'В эксплуатации'),
                        ('maintenance', 'На обслуживании'),
                        ('repair', 'В ремонте'),
                        ('decommissioned', 'Списано'),
                        ('storage', 'На складе'),
                    ],
                    default='active',
                    max_length=20,
                    verbose_name='Статус',
                )),
                ('specifications', models.JSONField(blank=True, default=dict, verbose_name='Технические характеристики')),
                ('passport_file', models.FileField(blank=True, null=True, upload_to='passports/', verbose_name='Паспорт')),
                ('notes', models.TextField(blank=True, verbose_name='Примечания')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Оборудование',
                'verbose_name_plural': 'Оборудование',
                'ordering': ['name'],
            },
        ),
    ]
