┌─────────────────────────────────────────────────────────────────────┐
│                        mqtt_cache.py                              │
├─────────────────────────────────────────────────────────────────────┤
│  1. 模块导入 & 配置参数                                            │
│  2. 全局缓存字典 (_cache)                                          │
│  3. 时间处理工具函数                                               │
│  4. 消息处理函数                                                   │
│  5. MQTT客户端连接与消息循环                                       │
│  6. 数据查询接口                                                   │
│  7. 数据库写入函数（新增）                                          │
└─────────────────────────────────────────────────────────────────────┘


1. 模块导入 & 配置参数

MQTT_BROKER_HOST	MQTT服务器地址	localhost
MQTT_BROKER_PORT	MQTT端口	1883
MQTT_TOPICS	订阅的主题列表	5个标准主题
MQTT_CLIENT_ID	客户端ID	django-overview-mqtt-client
MQTT_ENABLED	是否启用MQTT	True


2. 全局缓存字典 (_cache)
3. 时间处理工具函数
4. 消息处理函数

函数	                                     功能
_normalize_payload(payload)	                将MQTT消息负载转换为JSON字典
_on_connect(client, userdata, flags, rc)	连接成功后的回调，订阅所有主题
_update_env(data)	                        更新环境数据缓存并写入数据库
_update_soil(data)	                        更新土壤数据缓存并写入数据库
_update_sensor(data)	                    更新传感器数据缓存并写入数据库
_update_devices(data)	                    更新设备列表缓存并写入数据库
_update_alarms(data)	                    更新告警列表缓存并写入数据库
_on_message(client, userdata, msg)	        收到消息后的路由分发



5. MQTT客户端启动函数
函数	        功能
_mqtt_runner()	MQTT客户端主循环（后台线程）
start_mqtt()	启动MQTT后台线程

6. 数据查询接口
函数	        功能                   返回值
get_latest_env()	获取最新环境数据	字典或None
get_latest_soil()	获取最新土壤数据	字典或None
get_latest_sensor()	获取最新传感器数据	字典或None
get_device_list()	获取设备列表	    列表
get_latest_alarms()	获取最新告警	    列表
get_env_history(hours)	获取指定小时内的环境历史	列表
get_soil_history(hours)	获取指定小时内的土壤历史	列表


7. 数据库写入函数（新增）

_save_env_record(data)	保存环境监测记录	EnvMonitorRecord
_save_soil_record(data)	保存土壤监测记录	SoilMonitorRecord
_save_sensor_data(data)	保存传感器数据	SensorData
_save_device_node(data)	保存/更新设备节点	DeviceNode
_save_alarm_record(data)	保存告警记录	AlarmRecord




┌─────────────────────────────────────────────────────────────────────┐
│                      mqtt_worker.py                               │
├─────────────────────────────────────────────────────────────────────┤
│  1. 模块导入                                                      │
│  2. Command类（Django管理命令）                                     │
│     - handle(): 主入口                                             │
│     - on_connect(): 连接回调                                       │
│     - on_message(): 消息处理（路由+入库）                           │
└─────────────────────────────────────────────────────────────────────┘

on_connect() 回调
```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # 连接成功，订阅所有主题
        for topic in topics:
            client.subscribe(topic)
    else:
        # 连接失败，记录错误
```

on_message() 回调
```python
def on_message(client, userdata, msg):
    # 1. 解码消息负载为JSON
    # 2. 根据主题路由到不同处理逻辑
    # 3. 写入数据库
```    


四.总体架构:


传感器设备 ──JSON──▶ MQTT Broker
                        │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   mqtt_cache.py    mqtt_worker.py   其他订阅者
        │                │
        ▼                ▼
   内存缓存          直接入库
        │                │
        ▼                ▼
   实时API响应      持久化存储
        │
        ▼
   frontend (前端展示)






五、关键技术点
1. 延迟导入机制
```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # 连接成功，订阅所有主题
        for topic in topics:
            client.subscribe(topic)
    else:
        # 连接失败，记录错误
```
2. 线程安全
使用 deque 作为历史队列（线程安全）
使用 threading.Thread(daemon=True) 启动后台线程
3. 容错处理
JSON解析失败时记录警告日志
数据库写入失败时记录错误日志但不中断服务
MQTT连接失败时优雅降级
4. 数据格式兼容性
支持多种时间戳格式（ISO、字符串、时间戳）
支持单个对象或数组格式的设备/告警数据
缺失字段使用合理默认值