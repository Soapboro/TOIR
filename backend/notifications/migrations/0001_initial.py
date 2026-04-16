import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('message', models.TextField(verbose_name='Текст')),
                ('notification_type', models.CharField(
                    choices=[
                        ('request_created', 'Создана заявка'),
                        ('request_assigned', 'Заявка назначена'),
                        ('request_status_changed', 'Статус заявки изменён'),
                        ('maintenance_due', 'Плановое ТО'),
                        ('maintenance_overdue', 'Просрочено ТО'),
                        ('failure_prediction', 'Прогноз неисправности'),
                        ('system', 'Системное'),
                    ],
                    default='system',
                    max_length=30,
                    verbose_name='Тип',
                )),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('related_object_type', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Получатель',
                )),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['-created_at'],
            },
        ),
    ]
