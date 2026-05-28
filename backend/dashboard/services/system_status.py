from django.conf import settings
from django.db import connection
from django.utils import timezone

from dashboard.models import (
    AlarmRecord,
    ChatSession,
    DeviceNode,
    EnvMonitorRecord,
    SensorData,
    SoilMonitorRecord,
)
from dashboard.services.mqtt_cache import get_mqtt_runtime_status, mqtt as paho_mqtt_module
from dashboard.services.overview import SAMPLING_INTERVAL


def _format_dt(value):
    if value is None:
        return None
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")


def _latest_db_record(model, time_field="recorded_at"):
    try:
        instance = model.objects.order_by(f"-{time_field}").first()
    except Exception:
        return None
    if instance is None:
        return None
    recorded = getattr(instance, time_field, None)
    node = getattr(instance, "node", None)
    node_id = getattr(node, "node_id", None) if node else None
    return {
        "at": _format_dt(recorded),
        "node_id": node_id,
        "id": instance.pk,
    }


def _check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {"status": "ok", "detail": "连接正常"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def build_system_status_payload():
    now = timezone.localtime(timezone.now())
    total_devices = DeviceNode.objects.count()
    online_devices = DeviceNode.objects.filter(status="online").count()
    offline_devices = max(total_devices - online_devices, 0)
    active_alarms = AlarmRecord.objects.filter(status="active").count()

    mqtt_enabled = getattr(settings, "MQTT_ENABLED", False)
    mqtt_runtime = get_mqtt_runtime_status()
    cache = mqtt_runtime.get("cache") or {}
    cache_has_data = any(
        [
            cache.get("env"),
            cache.get("soil"),
            cache.get("sensor"),
            cache.get("device_count", 0) > 0,
        ]
    )

    if not mqtt_enabled:
        mqtt_state = "disabled"
        mqtt_detail = "（如要启用，请将.env 文件中设置 MQTT_ENABLED=true）"
    elif paho_mqtt_module is None:
        mqtt_state = "error"
        mqtt_detail = "缺少 paho-mqtt 依赖"
    elif mqtt_runtime.get("thread_alive"):
        mqtt_state = "running"
        mqtt_detail = "进程内订阅线程运行中"
    elif cache_has_data:
        mqtt_state = "cache_only"
        mqtt_detail = "缓存有数据，订阅线程未运行"
    else:
        mqtt_state = "idle"
        mqtt_detail = "已启用，等待数据或检查 Broker 连接"

    llm_key = getattr(settings, "LLM_API_KEY", "") or ""
    llm_base = getattr(settings, "LLM_API_BASE", "") or ""

    env_db = _latest_db_record(EnvMonitorRecord)
    soil_db = _latest_db_record(SoilMonitorRecord)
    sensor_db = _latest_db_record(SensorData, time_field="created_at")

    mqtt_latest = mqtt_runtime.get("latest") or {}

    return {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "active_alarms": active_alarms,
            "sampling_interval": SAMPLING_INTERVAL,
        },
        "services": {
            "api": {"status": "ok", "detail": "Django API 正常响应"},
            "database": _check_database(),
            "mqtt": {
                "status": mqtt_state,
                "detail": mqtt_detail,
                "enabled": mqtt_enabled,
                "thread_alive": mqtt_runtime.get("thread_alive", False),
                "broker_host": getattr(settings, "MQTT_BROKER_HOST", ""),
                "broker_port": getattr(settings, "MQTT_BROKER_PORT", 1883),
                "topics": list(getattr(settings, "MQTT_TOPICS", [])),
                "auth_configured": bool(getattr(settings, "MQTT_USERNAME", "")),
                "paho_installed": paho_mqtt_module is not None,
            },
            "llm": {
                "status": "ok" if llm_key else "unconfigured",
                "detail": "已配置 API Key" if llm_key else "未配置 LLM_API_KEY / OPENAI_API_KEY",
                "model": getattr(settings, "LLM_MODEL", ""),
                "api_base_set": bool(llm_base),
            },
        },
        "data_freshness": {
            "env": {
                "cache_at": mqtt_latest.get("env_at"),
                "cache_node_id": mqtt_latest.get("env_node_id"),
                "database": env_db,
            },
            "soil": {
                "cache_at": mqtt_latest.get("soil_at"),
                "cache_node_id": mqtt_latest.get("soil_node_id"),
                "database": soil_db,
            },
            "sensor": {
                "cache_at": mqtt_latest.get("sensor_at"),
                "database": sensor_db,
            },
        },
        "mqtt_cache": cache,
        "database_stats": {
            "device_nodes": total_devices,
            "env_records": EnvMonitorRecord.objects.count(),
            "soil_records": SoilMonitorRecord.objects.count(),
            "sensor_records": SensorData.objects.count(),
            "alarm_records": AlarmRecord.objects.count(),
            "active_alarm_records": active_alarms,
            "chat_sessions": ChatSession.objects.count(),
        },
    }
