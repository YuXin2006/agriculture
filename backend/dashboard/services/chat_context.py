from dashboard.models import AlarmRecord, DeviceNode
from dashboard.services.mqtt_cache import get_latest_env, get_latest_soil, get_latest_sensor


def build_agri_context_text() -> str:
    """汇总当前监测数据，供 LangChain 系统提示词使用。"""
    total = DeviceNode.objects.count()
    online = DeviceNode.objects.filter(status="online").count()
    offline = max(total - online, 0)

    lines = [
        f"设备概况：共 {total} 台，在线 {online} 台，离线 {offline} 台",
    ]

    env = get_latest_env()
    soil = get_latest_soil()
    sensor = get_latest_sensor()

    if env:
        lines.append(
            "最新环境数据："
            f"空气温度 {env.temperature}℃，空气湿度 {env.humidity}%，"
            f"CO₂ {env.co2} ppm，光照 {env.light} lux，"
            f"大气压 {env.pressure} kPa，空气质量指数 {env.air_quality}"
        )
    elif sensor:
        lines.append(
            "最新传感器数据："
            f"温度 {sensor.temperature}℃，CO₂ {sensor.co2} ppm，"
            f"光照 {sensor.light} lux，土壤湿度 {sensor.soil_moisture}%"
        )
    else:
        lines.append("最新环境数据：暂无")

    if soil:
        lines.append(
            f"最新土壤数据：湿度 {soil.soil_moisture}%，pH {soil.soil_ph}，土温 {soil.soil_temperature}℃"
        )
    else:
        lines.append("最新土壤数据：暂无")

    active_alarms = AlarmRecord.objects.filter(status="active").order_by("-created_at")[:5]
    if active_alarms:
        lines.append("未处理告警（最近 5 条）：")
        for alarm in active_alarms:
            detail = alarm.message or alarm.detail or ""
            lines.append(f"  - [{alarm.level}] {alarm.title}：{detail}".strip())
    else:
        lines.append("未处理告警：无")

    return "\n".join(lines)
