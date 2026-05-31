import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agri_backend.settings')

# 配置 Django
import django
django.setup()


from datetime import datetime, timedelta
from django.utils import timezone
from dashboard._utils.async_redis_client import async_redis_client
from dashboard._utils.redis_keys import *  # 复用现有缓存键定义


# 异步获取最新数据
async def async_get_latest_env():
    """异步获取最新环境数据"""
    cached = await async_redis_client.hgetall(KEY_LATEST_ENV)
    if cached:
        return cached
    # 降级到数据库（异步查询）
    from dashboard.models import EnvMonitorRecord
    try:
        record = await EnvMonitorRecord.objects.order_by("-recorded_at").afirst()
        return record.__dict__ if record else None
    except Exception:
        return None

async def async_get_latest_soil():
    """异步获取最新土壤数据"""
    cached = await async_redis_client.hgetall(KEY_LATEST_SOIL)
    if cached:
        return cached
    from dashboard.models import SoilMonitorRecord
    try:
        record = await SoilMonitorRecord.objects.order_by("-recorded_at").afirst()
        return record.__dict__ if record else None
    except Exception:
        return None

async def async_get_env_history(hours=24):
    """异步获取环境历史数据"""
    cutoff = timezone.now() - timedelta(hours=hours)
    history = await async_redis_client.lrange(KEY_HISTORY_ENV)
    if history:
        return [h for h in history if datetime.fromisoformat(h.get("recorded_at", "").replace("Z", "+00:00")) >= cutoff]
    return []