from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'
    verbose_name = 'Техническое обслуживание'

    def ready(self):
        # Запускаем планировщик только в основном процессе
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            try:
                from .scheduler import start
                start()
            except Exception as e:
                print(f'[scheduler] Не удалось запустить: {e}')
