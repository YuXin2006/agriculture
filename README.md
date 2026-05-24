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
