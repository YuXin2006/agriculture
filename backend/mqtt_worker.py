import os
import time
import json
import redis
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MQTTWorker:
    def __init__(self):
        # 初始化 Redis 连接（用于存储消息）
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
        # 初始化 MQTT 客户端
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # 设置 MQTT 认证
        username = os.getenv("MQTT_USERNAME")
        password = os.getenv("MQTT_PASSWORD")
        if username and password:
            self.client.username_pw_set(username, password)
        
        # 设置心跳间隔（60秒）
        self.client.keepalive = 60
        
        # 连接状态标志，避免重复打印失败日志
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """连接成功后的回调"""
        if rc == 0:
            # 连接成功
            if not self.connected:
                print(f"✅ MQTT Connected with result code {rc}")
                self.connected = True
            # 订阅所有农业相关主题
            topics = [
                ("agri/env", 0),
                ("agri/soil", 0),
                ("agri/alarm", 0),
                ("agri/device", 0),
            ]
            client.subscribe(topics)
            if self.connected:
                print(f"📩 Subscribed to topics: {[t[0] for t in topics]}")
        else:
            # 连接失败
            if not self.connected:
                print(f"❌ MQTT Connect failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """收到消息后的处理"""
        try:
            # 解析消息
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload) if payload.startswith("{") else {"raw": payload}
            
            # 获取 topic 后缀作为数据类型
            topic_suffix = msg.topic.split("/")[-1] if "/" in msg.topic else msg.topic
            
            # 存储到 Redis（与 Django 后端一致的键格式）
            # 1. 发布到 Redis 频道（实时推送）
            self.redis_client.publish(f"mqtt:{msg.topic}", json.dumps(data))
            # 2. 存储最新值（供查询）- 使用 Django 期望的键格式
            if topic_suffix in ["env", "soil", "sensor"]:
                self.redis_client.set(f"agri:latest:{topic_suffix}", json.dumps(data), ex=600)
            elif topic_suffix == "alarm":
                # 告警使用列表存储
                self.redis_client.lpush("agri:latest:alarms", json.dumps(data))
                self.redis_client.ltrim("agri:latest:alarms", 0, 49)
                self.redis_client.expire("agri:latest:alarms", 3600)
            # 3. 追加到历史列表
            if topic_suffix in ["env", "soil"]:
                self.redis_client.lpush(f"agri:history:{topic_suffix}", json.dumps(data))
                self.redis_client.ltrim(f"agri:history:{topic_suffix}", 0, 287)
                self.redis_client.expire(f"agri:history:{topic_suffix}", 86400)
            
            print(f"📥 Processed: {msg.topic} -> Redis (key: agri:latest:{topic_suffix})")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        """断开连接后的处理"""
        if self.connected:
            print(f"🔌 MQTT Disconnected with result code {rc}")
            self.connected = False
        # 5秒后自动重连
        time.sleep(5)
        self.connect()
    
    def connect(self):
        """连接到 MQTT Broker"""
        host = os.getenv("MQTT_BROKER_HOST", "iot.skyate.com")
        port = int(os.getenv("MQTT_BROKER_PORT", 1883))
        
        try:
            if not self.connected:
                print(f"🔗 Connecting to MQTT Broker: {host}:{port}")
            self.client.connect(host, port, self.client.keepalive)
            # 开始无限循环处理消息
            self.client.loop_forever()
        except Exception as e:
            if not self.connected:
                print(f"❌ MQTT Connection failed: {e}")
            time.sleep(5)
            self.connect()

if __name__ == "__main__":
    print("🚀 Starting MQTT Worker...")
    worker = MQTTWorker()
    worker.connect()