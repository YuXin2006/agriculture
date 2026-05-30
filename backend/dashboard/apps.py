import threading
from django.apps import AppConfig
from django.conf import settings

class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        
        # 启动 MQTT 客户端
        if getattr(settings, "MQTT_ENABLED", False):
            from dashboard.services.mqtt_cache import start_mqtt
            start_mqtt()  
        # 延迟1秒后在后台线程中执行缓存预热
        # 避免在应用初始化期间访问数据库
        threading.Timer(1.0, self._start_warmup).start()
    
    def _start_warmup(self):
        """在后台线程中执行缓存预热"""
        try:
            from dashboard.services.chat_cache import warmup_chat_cache
            warmup_chat_cache()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"缓存预热启动失败: {e}")