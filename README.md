# Vue + Django 前后端分离示例（农业监测系统）

## 项目结构

- `frontend/`：Vue 3 + Vite 前端
- `backend/`：Django 后端

<!-- ## 1. 启动后端（Django）

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

后端接口示例：

- `GET http://127.0.0.1:8000/api/overview/`

## 2. 启动前端（Vue）

```bash
cd frontend
npm install
npm run dev
``` -->
一键启动项目
```bash
npm run dev
```
默认打开 `http://127.0.0.1:5173/`，首页即“数据总览”页面。

## 页面说明

- 数据总览：基地总览看板；右上角可点击天气条查看近 7 日预报（见下文「天气预报」）
- 设备管理：可自行对设备增删改查
- 告警中心：完整的告警功能页面
- 系统设置：空白占位页
- 问问ai:一个chatbot可根据上传的数据进行分析


### 部分后端接口声明

1. overview/：获取数据总览信息 返回格式如下

{
    "meta": {
        "location": "示范种植基地 · 北区",
        "last_updated": "2024-01-15 14:30:00",
        "weather": {"text": "晴", "temperature": 26.5, "icon": "☀"},
        "sampling_interval": "5 分钟/次"
    },
    "metrics": {
        "soil_moisture": 58.2,
        "temperature": 25.8,
        "co2": 420,
        "light": 8500
    },
    "summary_stats": [
        {"icon": "📡", "label": "设备总数", "value": 25},
        {"icon": "✅", "label": "在线设备", "value": 23},
        {"icon": "⚠", "label": "离线设备", "value": 2},
        {"icon": "⏱", "label": "采集频率", "value": "5 分钟/次"}
    ],
    "summary": {
        "total_devices": 25,
        "online_devices": 23,
        "offline_devices": 2,
        "alarm_count": 3,
        "sampling_interval": "5 分钟/次"
    },
    "sensor_cards": [...],  # 8个传感器卡片数据
    "alarms": [...],         # 最近5条告警
    "chart_24h": {           # 24小时趋势图
        "labels": ["00:00", "01:00", ...],
        "temperature": [22.1, 21.8, ...],
        "humidity": [65, 66, ...],
        "soil_moisture": [58, 57, ...]
    },
    "air_quality_distribution": {...},
    "kpi_stats": [...],      # KPI统计
    "devices": {             # 分页设备列表
        "results": [...],
        "pagination": {...},
        "summary": {...}
    },
    "heatmap": {...},        # 土壤湿度热力图
    "gps_points": [...]      # GPS点位列表
}

2. sensors/ 传感器数据的 列表查询 和 创建 操作。


{
    "results": [...],  # 传感器数据列表
    "pagination": {
        "page": 1,
        "page_size": 10,
        "total": 100,
        "total_pages": 10
    }
}


3. sensors/<int:pk>/ 传感器数据的 详情查询 和 更新 操作。

### 拟定的mqtt数据主题

1.  环境数据主题：agri/env (对应EnvMonitorRecord模型)
{
    "node_id": "sensor_001",
    "temperature": 25.8,
    "humidity": 65.2,
    "co2": 420,
    "light": 8500,
    "pressure": 101.3,
    "air_quality": 45,
    "recorded_at": "2024-01-15 14:30:00"
}


2.  土壤湿度主题：agri/soil (对应SoilMoistureRecord模型)
{
    "node_id": "sensor_001",
    "soil_moisture": 58.5,
    "soil_ph": 6.8,
    "soil_temperature": 22.3,
    "recorded_at": "2024-01-15 14:30:00"
}

3.  传感器综合数据主题：agri/sensor (对应SensorData模型)
{
    "node_id": "sensor_001",
    "temperature": 25.5,
    "humidity": 65.2,
    "co2": 420,
    "light": 8500,
    "soil_moisture": 58.0,
    "soil_ph": 6.8,
    "created_at": "2024-01-15T14:30:00Z"
}

4. 设备信息主题：agri/devices (对应DeviceNode模型)
{
    "node_id": "sensor_001",
    "name": "温室A区-传感器01",
    "device_type": "多合一传感器",
    "region": "北区",
    "install_location": "温室A区-第3排",
    "status": "online",
    "signal_strength": 4,
    "battery_level": 85,
    "latitude": 30.5928,
    "longitude": 104.0668,
    "updated_at": "2024-01-15 14:30:00"
}

5. (拟定) 告警数据主题：agri/alarm (对应AlarmRecord模型)
{
    "node_id": "sensor_001",
    "level": "warn",
    "title": "土壤湿度过低",
    "message": "当前土壤湿度为 35%，低于阈值 45%",
    "detail": "建议立即启动灌溉系统",
    "metric_value": 35.0,
    "threshold": 45.0,
    "status": "active",
    "created_at": "2024-01-15 14:30:00"
}

## ai功能
--------------ai功能(chatbot)------------------------------------
前端接口
sendChatMessage(data)	POST /api/chat/	发送消息
getChatHistory(params)	GET /api/chat/history/	获取历史
clearChatSession(data)	POST /api/chat/clear/	清空会话

发送消息的请求体约定：
{ message: "用户问题", session_id: "可选，多轮对话用" }

期望响应字段（后端实现时对齐即可）：
{ reply: "AI 回复", session_id: "会话 ID" }

后端实现
API 路由（对应 dashboard.js）
接口	              方法	                  说明
/api/chat/	          POST	                 发送消息，返回 { reply，session_id }
/api/chat/history/	  GET	                 按 session_id 拉取历史
/api/chat/clear/	  POST	                 清空会话并返回新 session_id

## 运维中心
-----------------运维中心-------------------------------------------
后端说明
  *新接口 GET /api/system/status/
   聚合返回：设备/告警摘要、API/数据库/MQTT/LLM 服务状态、各通道数据新鲜度、MQTT 缓存概况、数据库记录统计。
  *新文件 backend/dashboard/services/system_status.py — 状态组装逻辑
  *新文件 backend/dashboard/views/system.py — API 视图
  *增强 mqtt_cache.py — 记录 MQTT 线程状态，并提供 get_mqtt_runtime_status() 供看板使用
前端说明
  *SystemSettings.vue — 运维看板页面（只读）
      1.顶部 4 张统计卡：在线设备、未处理告警、MQTT 状态、采集频率
      2.服务状态：API、数据库、MQTT、大模型
      3.数据采集：env/soil/sensor 最近时间与来源（缓存 vs 数据库）
      4.MQTT 订阅主题、缓存概况、数据库统计
      5.快捷入口跳转总览/设备/告警/AI
      6.每 30 秒自动刷新，可手动刷新
  *dashboard.js — 新增 getSystemStatus()
## 告警记录
--------------------告警记录--------------------------
数据模型对应
字段	                    页面用途
node / node_id	            表单下拉选择节点；列表显示节点编号
level (info/warn/critical)	表单选择与彩色标签
title / message / detail	登记表单 + 列表展示
metric_value / threshold	表单数值输入；列表显示「当前值 · 阈值」
status (active/resolved)	表单与状态标签；一键「处理」
created_at	                列表告警时间

前端页面说明
frontend/src/views/AlarmCenter.vue（由空白页改为完整功能页）
统计卡片：告警总数、当前页未处理数、当前页严重数
登记表单：支持新增/编辑，字段与 AlarmSerializer 一致
告警列表：分页表格（每页 10 条，与后端 default_page_size 一致）
快捷操作：「处理」将状态改为 resolved；编辑、删除
交互：顶部 Toast 提示、刷新、分页跳转（与设备管理页相同模式）
样式：dash-card、深色表单、级别/状态标签色（与总览页告警配色一致）
## 天气预报
--------------------天气预报（数据总览）--------------------------
功能说明
  * 入口：数据总览页（Overview）右上角天气条，点击打开弹窗
  * 展示：所选城市近 7 日每日天气（emoji + 晴/多云/雨/雪/冰雹等）、最低/最高气温，以及日出、日落时间
  * 头部天气条：显示当前城市的实时气温与简要天气描述（晴/多云/雨等）
  * 城市选择：下拉框切换；范围为中国各省省会 + 深圳（北上广深中深圳单独列出）
  * 记忆：上次选择的城市保存在浏览器 localStorage，键名 weather_city_id，默认北京

数据来源（前端直连，无需后端接口与 API Key）
  * 使用 Open-Meteo 免费预报 API：https://open-meteo.com/
  * 请求示例（由前端按城市经纬度拼接）：
    GET https://api.open-meteo.com/v1/forecast
      ?latitude=39.90&longitude=116.40
      &current=temperature_2m,weather_code
      &daily=temperature_2m_max,temperature_2m_min,sunrise,sunset
      &timezone=Asia/Shanghai
      &forecast_days=7

涉及文件（维护时主要改这里）
  * frontend/src/components/WeatherModal.vue — 城市列表 CITIES、弹窗 UI、Open-Meteo 请求与解析
  * frontend/src/views/Overview.vue — 天气按钮、引入 WeatherModal、接收 summary 更新头部显示



天气预报功能数据流图：

用户选择城市
     ↓
onCityChange() 触发
     ↓
localCityId 更新
     ↓
┌─────────────┐    ┌─────────────────┐
│ localStorage│    │ emit(update:cityId) │
└─────────────┘    └─────────────────┘
                          ↓
                     watch 监听到变化
                          ↓
                     load(cityId)
                          ↓
                fetchForecast(cityId)
                          ↓
              ┌─────────────────────┐
              │ Open-Meteo API 请求 │
              └─────────────────────┘
                          ↓
              ┌─────────────────────┐
              │ 解析数据 → daily[]  │
              └─────────────────────┘
                          ↓
              ┌─────────────────────┐
              │ emit(summary) 通知  │
              │    父组件更新天气条   │
              └─────────────────────┘
--------------

## 缓存设计方案

核心架构-三个存储层:redis,_cache内存降级缓存.数据库

---------------redis数据类型和缓存键设计--------------------------
缓存键设计               对应的表
agri:latest:env         EnvMonitorRecord     hash
agri:latest:soil        SoilMonitorRecord    hash
agri:latest:sensor      SensorData           hash
agri:latest:alarms      AlarmRecord          list

agri:history:env        EnvMonitorRecord      list
agri:history:soil       SoilMonitorRecord     list

agri:summary            多表聚合               string

1. 
redis_client的redis缓存操作设计

其他函数说明
_test_connection(self) — 测试连接是否成功
_execute(self, func, *args, **kwargs) — 处理异常的统一执行方法


主要函数说明  :
hash类型操作
hset(self,key,data,expire)
hgetall(self,key)

list类型操作
lpush(self,key,data,maxlen,expire) <span style="color:red;"> （用到了pipeline对象）</span>
lrange(self,key,start,end=-1) <span style="color:red;"> （json->python对象 json.loads方法 python对象->json json.dumps方法）</span>

string类型操作
set(self,key,value,expire)
get(self,key)

2.  
mqtt_cache(services层的redis应用)

通过_cache字典实现设计了内存降级缓存 

主要函数更改说明:
  _update_env
   先更新redis缓存
  ```python
  redis_client.hset(KEY_LATEST_ENV, data,   expire=EXPIRE_LATEST_DATA)
  redis_client.lpush(KEY_HISTORY_ENV, data, maxlen=HISTORY_WINDOW_SIZE, expire=EXPIRE_HISTORY)
  ```
   再更新_cache缓存
  ```python
  _cache[KEY_LATEST_ENV] = data
  ```
   最后更新数据库缓存
   ```python
   EnvMonitorRecord.objects.create(**data)
   ```


  _update_soil
  _update_sensor
  _update_devices
  _update_alarms


其他函数说明
_mqtt_runner()
<span style="color:red;"> 
client.loop_forever()	阻塞式循环：持续监听消息（直到断开连接）
<span style="color:red;"> 
start_mqtt()

```python
_mqtt_thread = threading.Thread(target=_mqtt_runner, daemon=True)
```
<span style="color:red;"> 
守护线程：当主线程结束时自动退出，适合后台任务

因为_mqtt_runner()是一个阻塞式循环，所以需要在守护线程中运行，否则会导致主线程阻塞，无法执行其他任务

MQTT 客户端需要持续监听消息，是一个典型的后台服务，当 Django 服务器关闭时，MQTT 连接自然应该断开


除了 MQTT 客户端，守护线程还常用于：

场景	    示例
后台监控	   定时检查系统状态
日志收集	   异步写入日志文件
缓存清理	   定时清理过期缓存
心跳检测	  定期发送心跳包

<span style="color:red;"> 

3. chatbot的缓存预热实现机制

缓存预热在 Django 应用启动时触发，通过 apps.py 的 ready() 方法实现：
```python
 threading.Timer(1.0, self._start_warmup).start()
 ```
延迟1秒后在后台线程中执行缓存预热,避免在应用初始化期间访问数据库

                                               -->warmup_session_list()     获取最近活跃的会话
_start_warmup() -->  warmup_chat_cache()       -->warmup_recent_messages()  获取最近活跃的会话消息 (使用 pipeline 批量缓存)
                                               -->warmup_system_faq()       用string类型的faq_data硬编码



4. redis_client添加连接池,支持高并发
   redis缓存优化使得overview接口吞吐量提升5.1倍（66.7 -> 338）
   并发量提升2.5倍（200 -> 500）
   loadtime从18ms到1ms
   
   
```python
 pool = redis.ConnectionPool(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                max_connections=50,  # 关键：增加连接池大小，支持高并发
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            cls._instance._client = redis.Redis(connection_pool=pool)
```            

5. 针对api/overview接口 重写异步fastapi接口/api/async/overview 
   首先改写redis_client和mqtt_cache, 实现async_redis_client 和 async_mqtt_cache 类
   
   异步协程优化overview接口,实现吞吐量提升（3.5倍 338->1220），并发量提升（4.4倍 500->2200）低并发状态下响应时间基本不变

   启动方式：未添加到npm run dev聚合命令,需要单独启动,新加端口并
   ```bash
   cd c:\Users\YuXin\Downloads\agriculture\backend
   uvicorn async_api:app --host 0.0.0.0 --port 8001 --reload
   ```
   

## websocket实时通信架构   
该项目采用 Django Channels 实现WebSocket实时通信，
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js)                           │
│         WebSocketClient.js ──► ws://localhost:8000/ws/sensor/  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端 (Django)                           
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   
│  │ ASGI Server │───►│ URL Router   │───►│ SensorConsumer   │ 
│  │   (asgi.py) │    │ (routing.py) │    │ (consumers.py)   │ 
│  └─────────────┘    └──────────────┘    └────────┬─────────┘ 
│                                                  │         
│                           ┌──────────────────────┴
│                           ▼                                 
│                   ┌───────────────┐                         
│                   │ Channel Layer │ ←── Redis Pub/Sub        
│                   │   (Redis)     │                         
│                   └───────┬───────┘                         
│                           │                                 
│                           ▼                                 
│              ┌────────────────────────┐                   
│              │   MQTT Worker Thread   │                   
│              │   (mqtt_cache.py)      │                   
│              │  接收传感器数据并广播   │                   
│              └────────────────────────┘                   
└─────────────────────────────────────────────────────────────


### 第一步：建立websocket全双工连接
1. 首先前端得发送一个类似ws://localhost:8000/ws/sensor/的请求
websocketclient类(websocketclient.js) 中的connect 方法会配置好wsUrl 
然后在前端api导出这个类，这个前端的ws连接的请求就会发送到后端
2. 后端的asgiworker需要处理这个新的请求 (不同与http请求)
因此我们需要改写asgi.py的application属性 让根据请求路径判断是否是ws请求 如果是的话就走websocket_urlpatterns路径 ,然后就到了routing.py这里
3. 顺着routing.py的这个路由ws/sensor/ 看到它对应的视图是SensorConsumer.asgi()_，这里后端就需要创建一个consumers.py文件 用于定义一个视图处理ws请求的逻辑，   这里的asgi()_方法是什么意思呢?查看源码就发现类似与django的as_view()方法 用于定义ws请求的视图
4. 接着就看到了SensorConsumer里的connect方法 这里是建立ws全双工连接的核心代码.
   connect()函数中（******************************）
   ```python
   await self.channel_layer.group_add(
            'sensor_updates',
            self.channel_name
        )
    ``` 
    由于channel_layer与redis进行交互，所以需要深层挖一下这段代码的底层。
    1. 首先 group_add方法先获取channel_name (如: 'websocket.send!xxx...') ，用set结构存储所有连接的channel_name
    2. 生成redis key 类似于'asgi:group:sensor_updates' ，用hash结构存储某一个channel_name的所有连接信息
    3. 最后将channel_name添加到redis key对应的set中
        从redis层执行了这样的命令:  SADD asgi:group:sensor_updates "websocket.send!xxx..." 
    4. (可选)给某一个channel连接信息设置过期时间    
    结果是这样的
    ```python 
    #组的 channel 列表 (Set 结构)
    asgi:group:sensor_updates = {
    "websocket.send!abc123",
    "websocket.send!def456",
    "websocket.send!ghi789"
    }
    # channel 对应的连接信息 (Hash 结构)
    asgi:channel:websocket.send!abc123 = {
        "reply_channel": "websocket.send!abc123",
        "expiry": "2024-01-01T12:00:00"
    }```
这样第一步就已经建立起了ws全双工连接，后续的通信就会通过这个连接进行.
结果是发送的信息被redis存储了 

### 第二步：接收传感器数据并广播到所有连接的客户端
1. mqtt_cache.py首先会开启websocket广播支持，就是这个核心函数broadcast_to_channel(channel_name, message)，我们再深度剖析一下这个函数的核心部分
   1. channel_layer = get_channel_layer() 创建了channel_layer实例 这里的channel_layer是根据settings.py中的CHANNEL_LAYERS的配置创建的。
   2. async_to_sync 为什么要突然把这个异步方法转成同步函数？ 因为channel_layer.group_send()是一个异步方法，而我们这里的mqtt线程是同步的，让这个函数转成同步函数才能在同步环境中运行
   3. group_send 的底层实现（******************************）
        1. 从redis获取组内所有的channel
          从redis层执行了这样的命令:  SMEMBERS asgi:group:sensor_updates   
        2. 遍历所有的channel，发送msg，也就是redis的publish命令
          从redis层执行了这样的命令:  PUBLISH asgi:channel:websocket.send!abc123 "msg"
        3. 在之前asgi worker启动时 内部的channel_redis会创建一个后台监听任务listener 然后这个listener会监听到这个消息  将这个消息放到消息队列中 websocket消息循环获取这个消息队列的消息并处理
2. 然后又回到了consumers.py的broadcast_message方法，这个方法就是处理这个消息的 然后发送给前端

### 第三步：前端（客户端）接收广播消息 然后实时更新渲染传感器数据 
前端部分与vue的trigger触发特性相关 不过多赘述


    

