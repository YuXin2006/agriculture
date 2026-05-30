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
  *路由页标题改为「运维看板」（侧边栏仍为「系统设置」）
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

get_mqtt_runtime_status()










