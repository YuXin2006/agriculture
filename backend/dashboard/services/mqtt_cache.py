import json
import logging
import threading
from collections import deque
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

# 导入Redis客户端和缓存键常量
from dashboard._utils.redis_client import redis_client
from dashboard._utils.redis_keys import *

# 延迟导入模型
DeviceNode = None
EnvMonitorRecord = None
SoilMonitorRecord = None
SensorData = None
AlarmRecord = None

def _lazy_import_models():
    """延迟导入数据库模型"""
    global DeviceNode, EnvMonitorRecord, SoilMonitorRecord, SensorData, AlarmRecord
    from dashboard.models import DeviceNode, EnvMonitorRecord, SoilMonitorRecord, SensorData, AlarmRecord

logger = logging.getLogger(__name__)

# MQTT配置
MQTT_BROKER_HOST = getattr(settings, "MQTT_BROKER_HOST", "iot.skyate.com")
MQTT_BROKER_PORT = getattr(settings, "MQTT_BROKER_PORT", 1883)
MQTT_TOPICS = getattr(settings, "MQTT_TOPICS", ["agri/env", "agri/soil", "agri/sensor", "agri/alarm", "agri/device"])
MQTT_CLIENT_ID = getattr(settings, "MQTT_CLIENT_ID", "BENBEN")
MQTT_ENABLED = getattr(settings, "MQTT_ENABLED", True)

# 内存降级缓存
_cache = {
    "env": None,
    "soil": None,
    "sensor": None,
    "devices": [],
    "alarms": [],
    "env_history": deque(maxlen=HISTORY_WINDOW_SIZE),
    "soil_history": deque(maxlen=HISTORY_WINDOW_SIZE),
}

def _normalize_payload(payload):
    """标准化MQTT消息负载"""
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", errors="ignore")
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {payload[:100]}")
            return None
    return payload

def _add_time(data):
    """为数据添加时间戳"""
    if "recorded_at" not in data and "created_at" not in data:
        data["recorded_at"] = timezone.localtime(timezone.now()).isoformat()
    return data

def _update_env(data):
    """更新环境数据"""
    if not isinstance(data, dict): return
    _add_time(data)
    
    # Redis缓存
    redis_client.hset(KEY_LATEST_ENV, data, expire=EXPIRE_LATEST_DATA)
    redis_client.lpush(KEY_HISTORY_ENV, data, maxlen=HISTORY_WINDOW_SIZE, expire=EXPIRE_HISTORY)
    
    # 内存缓存
    _cache["env"] = data
    _cache["env_history"].append(data)
    
    # 数据库
    try:
        node = DeviceNode.objects.get_or_create(node_id=data.get("node_id"))[0] if data.get("node_id") else None
        EnvMonitorRecord.objects.create(
            node=node,
            temperature=float(data.get("temperature", 0.0)),
            humidity=float(data.get("humidity", 0.0)),
            co2=float(data.get("co2", 0.0)),
            light=float(data.get("light", 0.0)),
            pressure=float(data.get("pressure", 101.3)),
            air_quality=int(data.get("air_quality", 50)),
        )
    except Exception as e:
        logger.error(f"Save env error: {e}")

def _update_soil(data):
    """更新土壤数据"""
    if not isinstance(data, dict): return
    _add_time(data)
    
    redis_client.hset(KEY_LATEST_SOIL, data, expire=EXPIRE_LATEST_DATA)
    redis_client.lpush(KEY_HISTORY_SOIL, data, maxlen=HISTORY_WINDOW_SIZE, expire=EXPIRE_HISTORY)
    
    _cache["soil"] = data
    _cache["soil_history"].append(data)
    
    try:
        node = DeviceNode.objects.get_or_create(node_id=data.get("node_id"))[0] if data.get("node_id") else None
        SoilMonitorRecord.objects.create(
            node=node,
            soil_moisture=float(data.get("soil_moisture", 0.0)),
            soil_ph=float(data.get("soil_ph", 6.8)),
            soil_temperature=float(data.get("soil_temperature", 20.0)),
        )
    except Exception as e:
        logger.error(f"Save soil error: {e}")

def _update_sensor(data):
    """更新传感器数据"""
    if not isinstance(data, dict): return
    _add_time(data)
    
    redis_client.hset(KEY_LATEST_SENSOR, data, expire=EXPIRE_LATEST_DATA)
    _cache["sensor"] = data
    
    try:
        SensorData.objects.create(
            soil_moisture=float(data.get("soil_moisture", 0.0)),
            temperature=float(data.get("temperature", 0.0)),
            co2=float(data.get("co2", 0.0)),
            light=float(data.get("light", 0.0)),
        )
    except Exception as e:
        logger.error(f"Save sensor error: {e}")

def _update_devices(data):
    """更新设备数据"""
    devices = [data] if isinstance(data, dict) else data
    for device in devices:
        if not isinstance(device, dict) or not device.get("node_id"):
            continue
        try:
            defaults = {
                "name": device.get("name", device["node_id"]),
                "device_type": device.get("device_type", "多合一传感器"),
                "region": device.get("region", ""),
                "status": device.get("status", "online"),
            }
            if device.get("latitude"):
                defaults["latitude"] = device["latitude"]
            if device.get("longitude"):
                defaults["longitude"] = device["longitude"]
            DeviceNode.objects.update_or_create(node_id=device["node_id"], defaults=defaults)
        except Exception as e:
            logger.error(f"Save device error: {e}")

def _update_alarms(data):
    """更新告警数据"""
    entries = [data] if isinstance(data, dict) else data
    for entry in entries:
        if not isinstance(entry, dict): continue
        _add_time(entry)
        
        redis_client.lpush(KEY_LATEST_ALARMS, entry, maxlen=50, expire=EXPIRE_ALARMS)
        _cache["alarms"].insert(0, entry)
        
        try:
            node = DeviceNode.objects.get_or_create(node_id=entry.get("node_id"))[0] if entry.get("node_id") else None
            AlarmRecord.objects.create(
                node=node,
                level=entry.get("level", "warn"),
                title=entry.get("title", "未知告警"),
                message=entry.get("message", ""),
                detail=entry.get("detail", ""),
                metric_value=float(entry["metric_value"]) if entry.get("metric_value") else None,
                threshold=float(entry["threshold"]) if entry.get("threshold") else None,
                status=entry.get("status", "active"),
            )
        except Exception as e:
            logger.error(f"Save alarm error: {e}")
    
    _cache["alarms"] = _cache["alarms"][:50]

def _on_message(client, userdata, msg):
    """处理MQTT消息"""
    if DeviceNode is None:
        _lazy_import_models()
    
    payload = _normalize_payload(msg.payload)
    if payload is None:
        return
    
    topic = msg.topic.lower()
    if topic.endswith("/env"):
        _update_env(payload)
    elif topic.endswith("/soil"):
        _update_soil(payload)
    elif topic.endswith("/sensor"):
        _update_sensor(payload)
    elif topic.endswith("/alarm"):
        _update_alarms(payload)
    elif topic.endswith("/device"):
        _update_devices(payload)

def _mqtt_runner():
    """MQTT客户端运行线程"""
    if mqtt is None:
        logger.warning("paho-mqtt not installed")
        return
    
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = lambda c, u, f, rc: [c.subscribe(t) for t in MQTT_TOPICS] if rc == 0 else logger.warning(f"MQTT connect failed: {rc}")
    client.on_message = _on_message
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_forever()
    except Exception as e:
        logger.exception(f"MQTT runner failed: {e}")

_mqtt_thread = None

def start_mqtt():
    """启动MQTT客户端"""
    global _mqtt_thread
    if not MQTT_ENABLED or (_mqtt_thread and _mqtt_thread.is_alive()):
        return
    _mqtt_thread = threading.Thread(target=_mqtt_runner, daemon=True)#创建守护线程，目标函数为 _mqtt_runner
    _mqtt_thread.start()

# ==================== 获取数据函数 ====================

def _get_cached(key, cache_key):
    """通用获取缓存函数"""
    cached = redis_client.hgetall(key) if key in [KEY_LATEST_ENV, KEY_LATEST_SOIL, KEY_LATEST_SENSOR] else redis_client.lrange(key)
    return cached if cached else _cache[cache_key]

def get_latest_env():
    return _get_cached(KEY_LATEST_ENV, "env") or (EnvMonitorRecord.objects.order_by("-recorded_at").first() if DeviceNode else None)

def get_latest_soil():
    return _get_cached(KEY_LATEST_SOIL, "soil") or (SoilMonitorRecord.objects.order_by("-recorded_at").first() if DeviceNode else None)

def get_latest_sensor():
    return _get_cached(KEY_LATEST_SENSOR, "sensor")

def get_latest_alarms():
    return _get_cached(KEY_LATEST_ALARMS, "alarms")

def get_device_list():
    return list(_cache["devices"])

def get_env_history(hours=24):
    cutoff = timezone.now() - timedelta(hours=hours)
    history = redis_client.lrange(KEY_HISTORY_ENV) or _cache["env_history"]
    return [h for h in history if datetime.fromisoformat(h.get("recorded_at", "").replace("Z", "+00:00")) >= cutoff] if history else []

def get_soil_history(hours=24):
    cutoff = timezone.now() - timedelta(hours=hours)
    history = redis_client.lrange(KEY_HISTORY_SOIL) or _cache["soil_history"]
    return [h for h in history if datetime.fromisoformat(h.get("recorded_at", "").replace("Z", "+00:00")) >= cutoff] if history else []

def get_mqtt_runtime_status():
    """获取MQTT运行状态"""
    return {
        "thread_alive": _mqtt_thread.is_alive() if _mqtt_thread else False,
        "cache": {
            "env": _cache["env"] is not None,
            "soil": _cache["soil"] is not None,
            "sensor": _cache["sensor"] is not None,
            "alarm_count": len(_cache["alarms"]),
        },
    }