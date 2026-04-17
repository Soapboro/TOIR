from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Добавляет статусы 'assigned' и 'closed' в RequestStatus.
    Изменение только на уровне choices (max_length=15 достаточно для всех значений).
    """

    dependencies = [
        ('repair_requests', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repairrequest',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Новая'),
                    ('assigned', 'Назначена'),
                    ('in_progress', 'В работе'),
                    ('on_hold', 'Приостановлена'),
                    ('completed', 'Выполнена'),
                    ('closed', 'Закрыта'),
                    ('cancelled', 'Отменена'),
                ],
                default='new',
                max_length=15,
                verbose_name='Статус',
            ),
        ),
    ]
