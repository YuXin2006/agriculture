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


def _update_soil(data):
    if not isinstance(data, dict):
        return
    _cache["soil"] = data
    _append_history(_cache["soil_history"], data)


def _update_sensor(data):
    if not isinstance(data, dict):
        return
    _cache["sensor"] = data


def _update_devices(data):
    if isinstance(data, dict):
        _cache["devices"] = [data]
    elif isinstance(data, list):
        _cache["devices"] = data


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
    _cache["alarms"] = _cache["alarms"][:50]


def _on_message(client, userdata, msg):
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
