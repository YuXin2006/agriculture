from django.apps import AppConfig
from django.conf import settings

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        

        if getattr(settings, "MQTT_ENABLED", False):
            from dashboard.services.mqtt_cache import start_mqtt

            start_mqtt()
