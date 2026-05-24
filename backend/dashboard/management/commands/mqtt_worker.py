import json
from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
from dashboard.models import DeviceTelemetry  # 引入你 dashboard 应用下的模型

class Command(BaseCommand):
    help = '启动 Django 后端 MQTT 长期订阅工作进程'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('正在初始化 MQTT 长期订阅服务...'))

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(self.style.SUCCESS('成功连接到 MQTT 服务器！'))
                # 订阅主题，+ 是通配符，代表订阅任意设备ID
                topic = "device/+/telemetry"
                client.subscribe(topic)
                self.stdout.write(f"已成功订阅主题: {topic}")
            else:
                self.stdout.write(self.style.ERROR(f'连接失败，错误码: {rc}'))

        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode('utf-8')
                data = json.loads(payload_str)
                
                self.stdout.write(f"收到数据: {data}")

                # 利用 Django ORM 存入数据库
                # 这里假设你的 models.py 里有名为 DeviceTelemetry 的类
                DeviceTelemetry.objects.create(
                    device_id=data.get('device_id', 'unknown'),
                    temperature=float(data.get('temp', 0.0)),
                    humidity=float(data.get('humi', 0.0)),
                    raw_data=data 
                )
                self.stdout.write(self.style.SUCCESS(f"数据已成功写入 db.sqlite3"))

            except json.JSONDecodeError:
                self.stdout.write(self.style.WARNING(f"解析失败，非标准 JSON: {msg.payload}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"入库异常: {str(e)}"))

        # 配置 MQTT 客户端
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        client.on_connect = on_connect
        client.on_message = on_message

        # 连接到 MQTTX 提供的公共免费测试服务器（测试用，后期换成你自己的云服务器地址）
        broker_address = "broker.emqx.io" 
        port = 1883
        
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