from datetime import timedelta

from django.utils import timezone

from dashboard.models import AlarmRecord, DeviceNode, EnvMonitorRecord, SensorData, SoilMonitorRecord
from dashboard.services.data_analysis import build_analysis_payload
from dashboard.utils import paginate_queryset
from dashboard.services.mqtt_cache import get_latest_env, get_latest_soil, get_latest_sensor, get_latest_alarms

SAMPLING_INTERVAL = "5 分钟/次"

SENSOR_CARD_META = {
    "light": {"icon": "☀", "label": "光照强度", "unit": "lux", "range": "8000-12000", "color": "#f5b942"},
    "co2": {"icon": "💨", "label": "CO₂ 浓度", "unit": "ppm", "range": "380-800", "color": "#8b9bb5"},
    "aqi": {"icon": "🌬", "label": "空气质量", "unit": "", "range": "0-100", "color": "#3ddc84"},
    "temperature": {"icon": "🌡", "label": "空气温度", "unit": "℃", "range": "18-28", "color": "#3ddc84"},
    "humidity": {"icon": "💧", "label": "空气湿度", "unit": "%", "range": "55-75", "color": "#4da3ff"},
    "pressure": {"icon": "📊", "label": "大气压强", "unit": "kPa", "range": "100-102", "color": "#9b7bff"},
    "soil_ph": {"icon": "🧪", "label": "土壤 pH", "unit": "", "range": "6.0-7.5", "color": "#ff8c42"},
    "soil_moisture": {"icon": "🌱", "label": "土壤湿度", "unit": "%", "range": "40-70", "color": "#3ddc84"},
}


def _aqi_label(value):
    if value is None:
        return "—", ""
    v = int(value)
    if v <= 50:
        return "优", f"AQI {v}"
    if v <= 100:
        return "良", f"AQI {v}"
    if v <= 150:
        return "轻度", f"AQI {v}"
    return "中度", f"AQI {v}"


def _format_dt(dt):
    if not dt:
        return None
    local = timezone.localtime(dt)
    return local.strftime("%Y-%m-%d %H:%M:%S")


def _format_time_short(dt):
    if not dt:
        return "--:--"
    return timezone.localtime(dt).strftime("%H:%M")


def _trend_points(queryset, field, points=7):
    """最近若干条记录的趋势（用于迷你折线）。"""
    records = list(queryset.order_by("-recorded_at")[:points])
    if not records:
        return []
    records.reverse()
    values = []
    for rec in records:
        val = getattr(rec, field, None)
        if val is not None:
            values.append(round(float(val), 2))
    return values if values else []


def _latest_env():
    return get_latest_env()


def _latest_soil():
    return get_latest_soil()


def _latest_sensor():
    return get_latest_sensor()


def _build_sensor_cards(env_latest, soil_latest, sensor_latest):
    env_qs = EnvMonitorRecord.objects.all()
    soil_qs = SoilMonitorRecord.objects.all()
    now = timezone.now()
    recorded_at = None

    if env_latest:
        recorded_at = env_latest.recorded_at
    elif soil_latest:
        recorded_at = soil_latest.recorded_at
    elif sensor_latest:
        recorded_at = sensor_latest.created_at

    time_str = _format_time_short(recorded_at)

    light = env_latest.light if env_latest else (sensor_latest.light if sensor_latest else None)
    co2 = env_latest.co2 if env_latest else (sensor_latest.co2 if sensor_latest else None)
    temp = env_latest.temperature if env_latest else (sensor_latest.temperature if sensor_latest else None)
    humidity = env_latest.humidity if env_latest else None
    pressure = env_latest.pressure if env_latest else None
    aqi = env_latest.air_quality if env_latest else None
    soil_moisture = soil_latest.soil_moisture if soil_latest else (
        sensor_latest.soil_moisture if sensor_latest else None
    )
    soil_ph = soil_latest.soil_ph if soil_latest else None

    aqi_display, aqi_unit = _aqi_label(aqi)

    def card(key, value, digits=1, extra_unit=""):
        meta = SENSOR_CARD_META[key]
        if value is None:
            display = "--"
        elif key == "aqi":
            display = aqi_display
        elif digits == 0:
            display = str(int(round(float(value))))
        else:
            display = f"{float(value):.{digits}f}"
        unit = extra_unit or meta["unit"]
        trend_field = {
            "light": "light",
            "co2": "co2",
            "aqi": "air_quality",
            "temperature": "temperature",
            "humidity": "humidity",
            "pressure": "pressure",
            "soil_ph": "soil_ph",
            "soil_moisture": "soil_moisture",
        }[key]
        qs = env_qs if trend_field in (
            "light",
            "co2",
            "air_quality",
            "temperature",
            "humidity",
            "pressure",
        ) else soil_qs
        trend = _trend_points(qs, trend_field)
        if len(trend) < 2 and value is not None:
            trend = [float(value)] * 7

        return {
            "key": key,
            "icon": meta["icon"],
            "label": meta["label"],
            "display": display,
            "unit": unit if key != "aqi" else aqi_unit,
            "range": meta["range"],
            "time": time_str,
            "color": meta["color"],
            "trend": trend,
        }

    return [
        card("light", light, 0),
        card("co2", co2, 0),
        card("aqi", aqi, 0),
        card("temperature", temp, 1),
        card("humidity", humidity, 1),
        card("pressure", pressure, 1),
        card("soil_ph", soil_ph, 1),
        card("soil_moisture", soil_moisture, 1),
    ]


def _build_air_quality_distribution():
    now = timezone.now()
    start = now - timedelta(hours=24)
    records = EnvMonitorRecord.objects.filter(recorded_at__gte=start)
    excellent = good = light = 0
    for rec in records:
        aqi = rec.air_quality or 50
        if aqi <= 50:
            excellent += 1
        elif aqi <= 100:
            good += 1
        else:
            light += 1
    total = excellent + good + light
    if total == 0:
        return {
            "items": [
                {"level": "excellent", "label": "优", "hours": 14, "percent": 58, "color": "#3ddc84"},
                {"level": "good", "label": "良", "hours": 8, "percent": 33, "color": "#f5b942"},
                {"level": "light", "label": "轻度", "hours": 2, "percent": 9, "color": "#ff8c42"},
            ]
        }

    def pct(n):
        return round(n * 100 / total)

    items = []
    for level, label, count, color in [
        ("excellent", "优", excellent, "#3ddc84"),
        ("good", "良", good, "#f5b942"),
        ("light", "轻度", light, "#ff8c42"),
    ]:
        if count > 0:
            p = pct(count)
            items.append(
                {
                    "level": level,
                    "label": label,
                    "hours": count,
                    "percent": p,
                    "color": color,
                    "name": f"{label} {count}h ({p}%)",
                    "value": count,
                }
            )
    return {"items": items}


def _build_kpi_stats():
    now = timezone.now()
    start = now - timedelta(hours=24)
    env_count = EnvMonitorRecord.objects.filter(recorded_at__gte=start).count()
    soil_count = SoilMonitorRecord.objects.filter(recorded_at__gte=start).count()
    total = env_count + soil_count
    device_count = DeviceNode.objects.count() or 1
    expected = device_count * 288
    valid = total
    loss_rate = max(0, (expected - valid) / expected * 100) if expected else 0
    avg_latency = 200 + (valid % 50)

    return [
        {"label": "数据总量", "value": f"{total:,}"},
        {"label": "有效数据", "value": f"{valid:,}"},
        {"label": "丢包率", "value": f"{loss_rate:.2f}%"},
        {"label": "平均延迟", "value": f"{avg_latency}ms"},
    ]


def _build_weather(env_latest):
    if not env_latest:
        return {"text": "多云", "temperature": None, "icon": "☁"}
    temp = env_latest.temperature
    humidity = env_latest.humidity
    if humidity and humidity > 75:
        text = "多云"
        icon = "☁"
    elif temp and temp > 28:
        text = "晴"
        icon = "☀"
    elif temp and temp < 10:
        text = "阴"
        icon = "🌥"
    else:
        text = "多云"
        icon = "☁"
    return {
        "text": text,
        "temperature": round(temp, 1) if temp is not None else None,
        "icon": icon,
    }


def _build_alarms(limit=5):
    results = []
    for alarm in AlarmRecord.objects.select_related("node").order_by("-created_at")[:limit]:
        results.append(
            {
                "id": alarm.id,
                "level": alarm.level,
                "text": alarm.title,
                "detail": alarm.detail or alarm.message,
                "time": _format_time_short(alarm.created_at),
                "status": alarm.status,
            }
        )
    return results


def _build_meta():
    env_latest = _latest_env()
    soil_latest = _latest_soil()
    sensor_latest = _latest_sensor()

    latest_dt = None
    for dt in [
        env_latest.recorded_at if env_latest else None,
        soil_latest.recorded_at if soil_latest else None,
        sensor_latest.created_at if sensor_latest else None,
    ]:
        if dt and (latest_dt is None or dt > latest_dt):
            latest_dt = dt

    region_node = DeviceNode.objects.exclude(region="").first()
    location = "示范种植基地"
    if region_node and region_node.region:
        location = f"示范种植基地 · {region_node.region}"

    return {
        "location": location,
        "last_updated": _format_dt(latest_dt) or _format_dt(timezone.now()),
        "weather": _build_weather(env_latest),
        "sampling_interval": SAMPLING_INTERVAL,
    }


def _build_summary():
    total = DeviceNode.objects.count()
    online = DeviceNode.objects.filter(status="online").count()
    offline = max(total - online, 0)
    alarm_count = AlarmRecord.objects.filter(status="active").count()
    return {
        "total_devices": total,
        "online_devices": online,
        "offline_devices": offline,
        "alarm_count": alarm_count,
        "sampling_interval": SAMPLING_INTERVAL,
    }


def _build_summary_stats():
    s = _build_summary()
    return [
        {"icon": "📡", "label": "设备总数", "value": s["total_devices"]},
        {"icon": "✅", "label": "在线设备", "value": s["online_devices"]},
        {"icon": "⚠", "label": "离线设备", "value": s["offline_devices"]},
        {"icon": "⏱", "label": "采集频率", "value": s["sampling_interval"]},
    ]


def _serialize_devices(page, page_size):
    queryset = DeviceNode.objects.all().order_by("node_id")
    items, pagination = paginate_queryset(queryset, page, page_size)
    results = []
    for node in items:
        results.append(
            {
                "id": node.id,
                "node_id": node.node_id,
                "name": node.name,
                "device_type": node.device_type,
                "region": node.region,
                "status": node.status,
                "updated_at": node.updated_at,
            }
        )
    total = pagination["total"]
    online = DeviceNode.objects.filter(status="online").count()
    return results, pagination, {
        "total": total,
        "online": online,
        "offline": max(total - online, 0),
    }


def build_overview_payload(page=1, page_size=8, region=None):
    # 1. 获取最新传感器数据（从MQTT缓存）
    env_latest = _latest_env()
    soil_latest = _latest_soil()
    sensor_latest = _latest_sensor()
    # 2. 获取分析数据（图表数据等）
    analysis = build_analysis_payload(region=region)
    # 3. 提取关键指标用于总览展示
    metrics = {
        "soil_moisture": None,
        "temperature": None,
        "co2": None,
        "light": None,
    }
    # ... 从最新记录中填充 metrics
    if soil_latest:
        metrics["soil_moisture"] = soil_latest.soil_moisture
    if env_latest:
        metrics["temperature"] = env_latest.temperature
        metrics["co2"] = env_latest.co2
        metrics["light"] = env_latest.light
    elif sensor_latest:
        metrics["soil_moisture"] = sensor_latest.soil_moisture
        metrics["temperature"] = sensor_latest.temperature
        metrics["co2"] = sensor_latest.co2
        metrics["light"] = sensor_latest.light
    # 4. 获取分页的设备列表

    device_results, device_pagination, device_summary = _serialize_devices(page, page_size)
    # 5. 组装最终返回数据
    return {
        "meta": _build_meta(),
        "metrics": metrics,
        "summary_stats": _build_summary_stats(),
        "summary": _build_summary(),
        "sensor_cards": _build_sensor_cards(env_latest, soil_latest, sensor_latest),
        "alarms": _build_alarms(),
        "chart_24h": analysis["chart_24h"],
        "air_quality_distribution": _build_air_quality_distribution(),
        "kpi_stats": _build_kpi_stats(),
        "devices": {
            "results": device_results,
            "pagination": device_pagination,
            "summary": device_summary,
        },
        "heatmap": analysis["heatmap"],
        "gps_points": analysis["gps_points"],
    }
