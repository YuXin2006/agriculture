import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone as dt_timezone, timedelta

from django.conf import settings
from django.utils import timezone

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover
    mqtt = None

# 延迟导入模型，避免Django启动时的导入问题
DeviceNode = None
EnvMonitorRecord = None
SoilMonitorRecord = None
SensorData = None
AlarmRecord = None

def _lazy_import_models():
    """延迟导入数据库模型"""
    global DeviceNode, EnvMonitorRecord, SoilMonitorRecord, SensorData, AlarmRecord
    from dashboard.models import (
        DeviceNode,
        EnvMonitorRecord,
        SoilMonitorRecord,
        SensorData,
        AlarmRecord,
    )

logger = logging.getLogger(__name__)

MQTT_BROKER_HOST = getattr(settings, "MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = getattr(settings, "MQTT_BROKER_PORT", 1883)
MQTT_TOPICS = getattr(
    settings,
    "MQTT_TOPICS",
    ["agri/env", "agri/soil", "agri/sensor", "agri/alarm", "agri/device"],
)
MQTT_CLIENT_ID = getattr(settings, "MQTT_CLIENT_ID", "django-overview-mqtt-client")
MQTT_ENABLED = getattr(settings, "MQTT_ENABLED", True)

_cache = {
    "env": None,
    "soil": None,
    "sensor": None,
    "devices": [],
    "alarms": [],
    "env_history": deque(maxlen=288),
    "soil_history": deque(maxlen=288),
}


def _make_timezone_aware(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return timezone.make_aware(value)
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=dt_timezone.utc).astimezone(timezone.get_current_timezone())
        except (OSError, OverflowError):
            return timezone.localtime(timezone.now())
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            try:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return timezone.localtime(timezone.now())
        if dt.tzinfo is None:
            return timezone.make_aware(dt)
        return dt
    return timezone.localtime(timezone.now())


def _extract_recorded_at(data):
    for key in ("recorded_at", "created_at", "timestamp", "time"):
        if key in data:
            return _make_timezone_aware(data[key])
    return timezone.localtime(timezone.now())


def _append_history(queue, data):
    entry = dict(data)
    entry["recorded_at"] = _extract_recorded_at(entry)
    queue.append(entry)


def _normalize_payload(payload):
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", errors="ignore")
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("MQTT payload is not valid JSON: %s", payload)
            return None
    return payload


def _on_connect(client, userdata, flags, rc):
    if rc != 0:
        logger.warning("MQTT connection failed with code %s", rc)
        return
    for topic in MQTT_TOPICS:
        client.subscribe(topic)
        logger.info("MQTT subscribed: %s", topic)


def _update_env(data):
    if not isinstance(data, dict):
        return
    _cache["env"] = data
    _append_history(_cache["env_history"], data)
    # 写入数据库
    _save_env_record(data)


def _update_soil(data):
    if not isinstance(data, dict):
        return
    _cache["soil"] = data
    _append_history(_cache["soil_history"], data)
    # 写入数据库
    _save_soil_record(data)


def _update_sensor(data):
    if not isinstance(data, dict):
        return
    _cache["sensor"] = data
    # 写入数据库
    _save_sensor_data(data)


def _update_devices(data):
    if isinstance(data, dict):
        _cache["devices"] = [data]
        # 写入数据库
        _save_device_node(data)
    elif isinstance(data, list):
        _cache["devices"] = data
        # 写入数据库（批量）
        for device in data:
            _save_device_node(device)


def _update_alarms(data):
    entries = []
    if isinstance(data, dict):
        entries = [data]
    elif isinstance(data, list):
        entries = data
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if "created_at" not in entry and "recorded_at" not in entry:
            entry["created_at"] = timezone.localtime(timezone.now())
        _cache["alarms"].insert(0, entry)
        # 写入数据库
        _save_alarm_record(entry)
    _cache["alarms"] = _cache["alarms"][:50]


def _on_message(client, userdata, msg):
    # 确保模型已导入
    if DeviceNode is None:
        _lazy_import_models()
    
    payload = _normalize_payload(msg.payload)
    if payload is None:
        return
    topic = msg.topic.lower()
    if topic.endswith("/env") or topic.endswith("env"):
        _update_env(payload)
    elif topic.endswith("/soil"):
        _update_soil(payload)
    elif topic.endswith("/sensor"):
        _update_sensor(payload)
    elif topic.endswith("/alarm"):
        _update_alarms(payload)
    elif topic.endswith("/device") or topic.endswith("/devices"):
        _update_devices(payload)


def _mqtt_runner():
    if mqtt is None:
        logger.warning("paho-mqtt is not installed; MQTT cache disabled.")
        return
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = _on_connect
    client.on_message = _on_message
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_forever()
    except Exception as exc:
        logger.exception("MQTT runner failed: %s", exc)


def start_mqtt():
    if not MQTT_ENABLED:
        return
    thread = threading.Thread(target=_mqtt_runner, daemon=True)
    thread.start()


def get_latest_env():
    return _cache["env"]


def get_latest_soil():
    return _cache["soil"]


def get_latest_sensor():
    return _cache["sensor"]


def get_device_list():
    return list(_cache["devices"])


def get_latest_alarms():
    return list(_cache["alarms"])


def get_env_history(hours=24):
    cutoff = timezone.localtime(timezone.now()) - timedelta(hours=hours)
    return [item for item in _cache["env_history"] if item["recorded_at"] >= cutoff]


def get_soil_history(hours=24):
    cutoff = timezone.localtime(timezone.now()) - timedelta(hours=hours)
    return [item for item in _cache["soil_history"] if item["recorded_at"] >= cutoff]


def _save_env_record(data):
    """保存环境监测记录到数据库"""
    try:
        node = None
        node_id = data.get("node_id")
        if node_id:
            node, _ = DeviceNode.objects.get_or_create(node_id=node_id)
        
        EnvMonitorRecord.objects.create(
            node=node,
            temperature=data.get("temperature", 0.0),
            humidity=data.get("humidity", 0.0),
            co2=data.get("co2", 0.0),
            light=data.get("light", 0.0),
            pressure=data.get("pressure", 101.3),
            air_quality=data.get("air_quality", 50),
        )
        logger.info(f"Saved env record for node: {node_id}")
    except Exception as e:
        logger.error(f"Failed to save env record: {e}")


def _save_soil_record(data):
    """保存土壤监测记录到数据库"""
    try:
        node = None
        node_id = data.get("node_id")
        if node_id:
            node, _ = DeviceNode.objects.get_or_create(node_id=node_id)
        
        SoilMonitorRecord.objects.create(
            node=node,
            soil_moisture=data.get("soil_moisture", 0.0),
            soil_ph=data.get("soil_ph", 6.8),
            soil_temperature=data.get("soil_temperature", 20.0),
        )
        logger.info(f"Saved soil record for node: {node_id}")
    except Exception as e:
        logger.error(f"Failed to save soil record: {e}")


def _save_sensor_data(data):
    """保存传感器数据到数据库"""
    try:
        SensorData.objects.create(
            soil_moisture=data.get("soil_moisture", 0.0),
            temperature=data.get("temperature", 0.0),
            co2=data.get("co2", 0.0),
            light=data.get("light", 0.0),
        )
        logger.info(f"Saved sensor data")
    except Exception as e:
        logger.error(f"Failed to save sensor data: {e}")


def _save_device_node(data):
    """保存/更新设备节点信息到数据库"""
    try:
        node_id = data.get("node_id")
        if not node_id:
            return
        
        defaults = {
            "name": data.get("name", node_id),
            "device_type": data.get("device_type", "多合一传感器"),
            "region": data.get("region", ""),
            "install_location": data.get("install_location", ""),
            "status": data.get("status", "online"),
            "signal_strength": data.get("signal_strength", 4),
            "battery_level": data.get("battery_level", 100),
        }
        
        # 只在有值时更新经纬度
        if "latitude" in data and data["latitude"] is not None:
            defaults["latitude"] = data["latitude"]
        if "longitude" in data and data["longitude"] is not None:
            defaults["longitude"] = data["longitude"]
        
        DeviceNode.objects.update_or_create(node_id=node_id, defaults=defaults)
        logger.info(f"Saved/updated device node: {node_id}")
    except Exception as e:
        logger.error(f"Failed to save device node: {e}")


def _save_alarm_record(data):
    """保存告警记录到数据库"""
    try:
        node = None
        node_id = data.get("node_id")
        if node_id:
            node, _ = DeviceNode.objects.get_or_create(node_id=node_id)
        
        AlarmRecord.objects.create(
            node=node,
            level=data.get("level", "warn"),
            title=data.get("title", "未知告警"),
            message=data.get("message", ""),
            detail=data.get("detail", ""),
            metric_value=data.get("metric_value"),
            threshold=data.get("threshold"),
            status=data.get("status", "active"),
        )
        logger.info(f"Saved alarm record for node: {node_id}")
    except Exception as e:
        logger.error(f"Failed to save alarm record: {e}")