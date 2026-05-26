import json
from django.core.management.base import BaseCommand
from django.utils import timezone
import paho.mqtt.client as mqtt

# 引入项目模型
from dashboard.models import (
    DeviceNode,
    EnvMonitorRecord,
    SoilMonitorRecord,
    SensorData,
    AlarmRecord,
)

class Command(BaseCommand):
    help = '启动 Django 后端 MQTT 长期订阅工作进程'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('正在初始化 MQTT 长期订阅服务...'))

        # 订阅主题列表
        topics = [
            "agri/env",
            "agri/soil", 
            "agri/sensor",
            "agri/alarm",
            "agri/device",
        ]

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS('成功连接到 MQTT 服务器！'))
                # 订阅所有主题
                for topic in topics:
                    client.subscribe(topic)
                    self.stdout.write(f"已成功订阅主题: {topic}")
            else:
                self.stdout.write(self.style.ERROR(f'连接失败，错误码: {rc}'))

        def _get_node(node_id):
            """获取或创建设备节点"""
            if not node_id:
                return None
            node, _ = DeviceNode.objects.get_or_create(node_id=node_id)
            return node

        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode('utf-8')
                data = json.loads(payload_str)
                topic = msg.topic.lower()
                
                self.stdout.write(f"收到主题 [{topic}] 的数据: {json.dumps(data)[:100]}...")

                # 根据主题处理数据
                if topic.endswith("/env") or topic.endswith("env"):
                    # 环境监测数据
                    node = _get_node(data.get("node_id"))
                    EnvMonitorRecord.objects.create(
                        node=node,
                        temperature=data.get("temperature", 0.0),
                        humidity=data.get("humidity", 0.0),
                        co2=data.get("co2", 0.0),
                        light=data.get("light", 0.0),
                        pressure=data.get("pressure", 101.3),
                        air_quality=data.get("air_quality", 50),
                    )
                    self.stdout.write(self.style.SUCCESS(f"环境数据已写入数据库"))

                elif topic.endswith("/soil"):
                    # 土壤监测数据
                    node = _get_node(data.get("node_id"))
                    SoilMonitorRecord.objects.create(
                        node=node,
                        soil_moisture=data.get("soil_moisture", 0.0),
                        soil_ph=data.get("soil_ph", 6.8),
                        soil_temperature=data.get("soil_temperature", 20.0),
                    )
                    self.stdout.write(self.style.SUCCESS(f"土壤数据已写入数据库"))

                elif topic.endswith("/sensor"):
                    # 综合传感器数据
                    SensorData.objects.create(
                        soil_moisture=data.get("soil_moisture", 0.0),
                        temperature=data.get("temperature", 0.0),
                        co2=data.get("co2", 0.0),
                        light=data.get("light", 0.0),
                    )
                    self.stdout.write(self.style.SUCCESS(f"传感器数据已写入数据库"))

                elif topic.endswith("/alarm"):
                    # 告警数据
                    node = _get_node(data.get("node_id"))
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
                    self.stdout.write(self.style.SUCCESS(f"告警数据已写入数据库"))

                elif topic.endswith("/device"):
                    # 设备信息
                    if isinstance(data, list):
                        devices = data
                    else:
                        devices = [data]
                    
                    for device in devices:
                        node_id = device.get("node_id")
                        if not node_id:
                            continue
                        defaults = {
                            "name": device.get("name", node_id),
                            "device_type": device.get("device_type", "多合一传感器"),
                            "region": device.get("region", ""),
                            "install_location": device.get("install_location", ""),
                            "status": device.get("status", "online"),
                            "signal_strength": device.get("signal_strength", 4),
                            "battery_level": device.get("battery_level", 100),
                        }
                        if "latitude" in device and device["latitude"] is not None:
                            defaults["latitude"] = device["latitude"]
                        if "longitude" in device and device["longitude"] is not None:
                            defaults["longitude"] = device["longitude"]
                        DeviceNode.objects.update_or_create(node_id=node_id, defaults=defaults)
                    self.stdout.write(self.style.SUCCESS(f"设备信息已写入数据库"))

            except json.JSONDecodeError:
                self.stdout.write(self.style.WARNING(f"解析失败，非标准 JSON: {msg.payload[:50]}..."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"入库异常: {str(e)}"))

        # 配置 MQTT 客户端
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        client.on_connect = on_connect
        client.on_message = on_message

        # 从配置读取MQTT参数（优先使用settings配置）
        from django.conf import settings
        broker_address = getattr(settings, "MQTT_BROKER_HOST", "broker.emqx.io")
        port = getattr(settings, "MQTT_BROKER_PORT", 1883)
        
        self.stdout.write(f"正在连接 MQTT 服务器: {broker_address}:{port}")
        
        try:
            client.connect(broker_address, port, keepalive=60)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"无法连接服务器: {e}"))
            return

        # 启动长期死循环监听
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('正在退出 MQTT 监听...'))
            client.disconnect()