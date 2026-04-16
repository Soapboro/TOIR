import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_maintenanceregulation'),
        ('maintenance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenanceplan',
            name='regulation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='schedules',
                to='equipment.maintenanceregulation',
                verbose_name='Регламент ТО',
            ),
        ),
    ]
