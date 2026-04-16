from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='full_name',
            field=models.CharField(blank=True, max_length=255, verbose_name='Полное имя'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Администратор'),
                    ('mechanic', 'Механик'),
                    ('operator', 'Оператор'),
                    ('manager', 'Менеджер'),
                ],
                default='operator',
                max_length=20,
            ),
        ),
        migrations.AlterModelOptions(
            name='user',
            options={
                'ordering': ['full_name'],
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
            },
        ),
    ]
