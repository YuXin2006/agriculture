from datetime import timedelta

from django.utils import timezone

from dashboard.services.mqtt_cache import get_device_list, get_env_history, get_soil_history


def _hour_labels():
    return [f"{h:02d}:00" for h in range(24)]


def _series_from_history(history, field, hours=24):
    """按小时聚合最近 24 小时数据；无数据时用合理占位序列。"""
    now = timezone.localtime(timezone.now())
    start = now - timedelta(hours=hours)
    labels = _hour_labels()
    values = []

    for hour in range(hours):
        slot_start = start + timedelta(hours=hour)
        slot_end = slot_start + timedelta(hours=1)
        bucket = [item[field] for item in history if slot_start <= item["recorded_at"] < slot_end and item.get(field) is not None]
        values.append(round(sum(bucket) / len(bucket), 2) if bucket else None)

    if all(v is None for v in values):
        return labels, _default_series(hours, field)

    last = 20.0
    filled = []
    for v in values:
        if v is None:
            filled.append(last)
        else:
            last = v
            filled.append(v)
    return labels, filled


def _default_series(hours, field):
    presets = {
        "temperature": [22, 22.5, 23, 23.5, 24, 24.8, 25.2, 25.8, 26, 26.2, 26, 25.5, 25, 24.5, 24, 23.5, 23, 22.8, 22.5, 22.2, 22, 21.8, 21.5, 21.2],
        "humidity": [70, 69, 68, 67, 66, 65, 64, 63, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 70, 69, 68, 67, 66, 65],
        "soil_moisture": [58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 42, 43, 44, 45, 46, 47],
    }
    base = presets.get(field, [50] * hours)
    return base[:hours]


def build_heatmap():
    """5x5 网格土壤湿度热力图（基于各区域节点最新土壤数据）。"""
    devices = get_device_list()[:25]
    grid = []
    soil_history = get_soil_history(hours=168)
    for idx, node in enumerate(devices):
        node_id = node.get("node_id")
        latest = None
        if node_id:
            node_records = [item for item in soil_history if item.get("node_id") == node_id]
            if node_records:
                latest = max(node_records, key=lambda item: item["recorded_at"])
        value = latest["soil_moisture"] if latest and latest.get("soil_moisture") is not None else 40 + (idx % 5) * 4
        grid.append(
            {
                "x": idx % 5,
                "y": idx // 5,
                "value": round(value, 1),
                "node_id": node.get("node_id"),
                "region": node.get("region", ""),
            }
        )
    while len(grid) < 25:
        i = len(grid)
        grid.append({"x": i % 5, "y": i // 5, "value": 42.0, "node_id": None, "region": ""})
    return {"grid_size": 5, "points": grid}


def build_gps_points():
    points = []
    for node in get_device_list():
        latitude = node.get("latitude")
        longitude = node.get("longitude")
        if latitude is None or longitude is None:
            continue
        points.append(
            {
                "id": node.get("id"),
                "node_id": node.get("node_id"),
                "name": node.get("name"),
                "latitude": latitude,
                "longitude": longitude,
                "status": node.get("status"),
                "region": node.get("region"),
            }
        )
    return points


def build_analysis_payload(region=None):
    """从数据库获取最近24小时的监测数据，按小时聚合。"""
    from dashboard.models import EnvMonitorRecord, SoilMonitorRecord
    
    now = timezone.localtime(timezone.now())
    start_time = now - timedelta(hours=24)
    
    # 获取环境监测数据
    env_records = EnvMonitorRecord.objects.filter(
        recorded_at__gte=start_time
    ).order_by('recorded_at')
    
    # 获取土壤监测数据
    soil_records = SoilMonitorRecord.objects.filter(
        recorded_at__gte=start_time
    ).order_by('recorded_at')
    
    # 按小时聚合数据（不使用默认值）
    temperature_data, temp_labels = _aggregate_by_hour_real(env_records, 'temperature', start_time)
    humidity_data, _ = _aggregate_by_hour_real(env_records, 'humidity', start_time)
    soil_moisture_data, _ = _aggregate_by_hour_real(soil_records, 'soil_moisture', start_time)
    
    # 使用有数据的标签（如果没有数据则返回空数组）
    labels = temp_labels if temp_labels else [f"{h:02d}:00" for h in range(24)]
    
    return {
        "chart_24h": {
            "labels": labels,
            "temperature": temperature_data,
            "humidity": humidity_data,
            "soil_moisture": soil_moisture_data,
        },
        "heatmap": build_heatmap(),
        "gps_points": build_gps_points(),
    }


def _aggregate_by_hour_real(records, field_name, start_time):
    """直接从数据库获取数据，不使用默认值填充。"""
    # 初始化24小时数据列表
    hourly_data = [None] * 24
    
    # 按小时分组
    for record in records:
        record_time = timezone.localtime(record.recorded_at)
        time_diff = (record_time - start_time).total_seconds()
        hour_slot = int(time_diff // 3600)
        
        if 0 <= hour_slot < 24:
            if hourly_data[hour_slot] is None:
                hourly_data[hour_slot] = []
            value = getattr(record, field_name, None)
            if value is not None:
                hourly_data[hour_slot].append(value)
    
    # 计算平均值，没有数据的时段返回 None
    result_values = []
    result_labels = []
    
    for i, values in enumerate(hourly_data):
        hour_label = f"{(start_time.hour + i) % 24:02d}:00"
        if values and len(values) > 0:
            avg_value = round(sum(values) / len(values), 2)
            result_values.append(avg_value)
            result_labels.append(hour_label)
        else:
            # 没有数据时返回 None（ECharts 会自动跳过）
            result_values.append(None)
            result_labels.append(hour_label)
    
    return result_values, result_labels