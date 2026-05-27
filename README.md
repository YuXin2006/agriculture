# Vue + Django 前后端分离示例（农业监测系统）

## 项目结构

- `frontend/`：Vue 3 + Vite 前端
- `backend/`：Django 后端

## 1. 启动后端（Django）

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
```

默认打开 `http://127.0.0.1:5173/`，首页即“数据总览”页面。

## 页面说明

- 数据总览：按设计图完成静态布局（使用占位数据）
- 设备管理：空白占位页
- 告警中心：空白占位页
- 系统设置：空白占位页
- 帮助中心：空白占位页


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
