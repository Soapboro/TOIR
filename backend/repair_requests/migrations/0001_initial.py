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
            name='RepairRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Тема')),
                ('description', models.TextField(verbose_name='Описание неисправности')),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Низкий'),
                        ('medium', 'Средний'),
                        ('high', 'Высокий'),
                        ('critical', 'Критический'),
                    ],
                    default='medium',
                    max_length=10,
                    verbose_name='Приоритет',
                )),
                ('status', models.CharField(
                    choices=[
                        ('new', 'Новая'),
                        ('in_progress', 'В работе'),
                        ('on_hold', 'Приостановлена'),
                        ('completed', 'Выполнена'),
                        ('cancelled', 'Отменена'),
                    ],
                    default='new',
                    max_length=15,
                    verbose_name='Статус',
                )),
                ('resolution_notes', models.TextField(blank=True, verbose_name='Описание выполненных работ')),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('equipment', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='repair_requests',
                    to='equipment.equipment',
                    verbose_name='Оборудование',
                )),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='created_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Автор',
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Ответственный исполнитель',
                )),
            ],
            options={
                'verbose_name': 'Заявка на ремонт',
                'verbose_name_plural': 'Заявки на ремонт',
                'ordering': ['-created_at'],
            },
        ),
    ]
