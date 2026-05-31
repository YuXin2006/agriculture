import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')

# 配置 Django
import django
django.setup()


import asyncio
from fastapi import FastAPI
from dashboard.services.async_mqtt_cache import (
    async_get_latest_env,
    async_get_latest_soil,
    async_get_env_history,
)



app = FastAPI(title="Agriculture Async API", version="1.0")

@app.get("/api/async/env/latest", tags=["环境监控"])
async def get_env_latest():
    """异步获取最新环境数据"""
    return await async_get_latest_env()

@app.get("/api/async/soil/latest", tags=["土壤监控"])
async def get_soil_latest():
    """异步获取最新土壤数据"""
    return await async_get_latest_soil()

@app.get("/api/async/env/history", tags=["环境监控"])
async def get_env_history(hours: int = 24):
    """异步获取环境历史数据"""
    return await async_get_env_history(hours=hours)

@app.get("/api/async/overview", tags=["总览数据"])
async def get_overview():
    """异步聚合接口 - 并行获取所有数据"""
    # 关键：并行执行多个异步任务
    env, soil, history = await asyncio.gather(
        async_get_latest_env(),
        async_get_latest_soil(),
        async_get_env_history(hours=24),
    )
    return {
        "env": env,
        "soil": soil,
        "history": history,
    }